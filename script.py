import re
import argparse
from jinja2 import Environment, FileSystemLoader


def parse_netlist(file_path):
    """Parse a KiCad netlist file and return a dictionary of connections, a set of references, and a dictionary of components."""
    connections = {}
    refs = set()
    components = {}
    
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        net_name = None
        ref = None  # Initialize ref to manage component details
        in_components_section = False
        in_nets_section = False
        
        for line in lines:
            line = line.strip()  # Remove leading/trailing whitespace

            # Skip irrelevant lines and headers
            if line.startswith('(nets'):
                in_nets_section = True
                in_components_section = False
                continue
            elif line.startswith('(components'):
                in_nets_section = False
                in_components_section = True
                continue
            
            # Detect net start
            if in_nets_section and line.startswith('(net'):
                net_match = re.match(r'\(net \(code "\d+"\) \(name "(.*?)"\)', line)
                if net_match:
                    net_name = net_match.group(1)
                    connections[net_name] = []
                    continue
            
            # Detect node connections
            if in_nets_section and line.startswith('(node'):
                node_match = re.match(r'\(node \(ref "(.*?)"\) \(pin "(.*?)"\)( \(pinfunction "(.*?)"\))?', line)
                if node_match:
                    ref = node_match.group(1)
                    pin = node_match.group(2)
                    pinfunction = node_match.group(4) if node_match.group(4) else ''
                    if net_name:
                        # Debug print statements
                        #print(f"Debug: Parsing node - ref: {ref}, pin: {pin}, pinfunction: {pinfunction}, net_name: {net_name}")
                        
                        connections.setdefault(net_name, []).append((pin, pinfunction, ref))
                        refs.add(ref)
            
            # Detect component definitions
            if in_components_section and line.startswith('(comp'):
                comp_match = re.match(r'\(comp \(ref "(.*?)"\)', line)
                if comp_match:
                    ref = comp_match.group(1)
                    components[ref] = {}
                continue
            
            # Handle component details
            if in_components_section and line.startswith('(value'):
                if ref:
                    value_match = re.match(r'\(value "(.*?)"\)', line)
                    if value_match:
                        components[ref]['value'] = value_match.group(1)
                continue
            
            if in_components_section and line.startswith('(description'):
                if ref:
                    desc_match = re.match(r'\(description "(.*?)"\)', line)
                    if desc_match:
                        components[ref]['description'] = desc_match.group(1)
    
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
    except Exception as e:
        print(f"Error: An unexpected error occurred while parsing {file_path} - {e}")
    
    return connections, refs, components



def count_components(components):
    """Count the number of components based on their reference prefixes."""
    counts = {
        'Capacitors': 0,
        'Resistors': 0,
        'ICs': 0,
        'FETs': 0,
        'Connectors': 0,
        'Inductors': 0,
        'Mounting Holes': 0,
        'TestPads': 0,
        'Fiducials': 0,
        'Diodes/LEDs': 0,
        'Crystals': 0,
        'Others': 0
    }

    processed_refs = set()  # Keep track of processed component references

    for ref in components:
        if ref in processed_refs:
            continue
        
        processed_refs.add(ref)

        if ref.startswith('C'):
            counts['Capacitors'] += 1
        elif ref.startswith('R'):
            counts['Resistors'] += 1
        elif ref.startswith('IC') or ref.startswith('U'):
            counts['ICs'] += 1
        elif ref.startswith('Q') or ref.startswith('T') or ref.startswith('FET'):
            counts['FETs'] += 1
        elif ref.startswith('J') or ref.startswith('GPIO'):
            counts['Connectors'] += 1
        elif ref.startswith('L'):
            counts['Inductors'] += 1
        elif ref.startswith('MH') or ref.startswith('H'):
            counts['Mounting Holes'] += 1
        elif ref.startswith('TP'):
            counts['TestPads'] += 1
        elif ref.startswith('FID'):
            counts['Fiducials'] += 1
        elif ref.startswith('D'):
            counts['Diodes/LEDs'] += 1
        elif ref.startswith('X'):
            counts['Crystals'] += 1
        else:
            counts['Others'] += 1

    return counts


def generate_stats(components):
    """Generate detailed statistics from the components."""
    stats = {
        'Total Refs': 0,
        'Total Capacitors': 0,
        'Total Resistors': 0,
        'Total ICs': 0,
        'Total FETs': 0,
        'Total Connectors': 0,
        'Total Inductors': 0,
        'Total Mounting Holes': 0,
        'Total TestPads': 0,
        'Total Fiducials': 0,
        'Total Diodes/LEDs': 0,
        'Total Crystals': 0,
        'Total Others': 0,
        'Total Nets': 0,  # This can be updated separately if needed
        'Total Components': 0
    }

    refs = set()
    detailed_components = {
        'Capacitors': [],
        'Resistors': [],
        'ICs': [],
        'FETs': [],
        'Connectors': [],
        'Inductors': [],
        'Mounting Holes': [],
        'TestPads': [],
        'Fiducials': [],
        'Diodes/LEDs': [],
        'Crystals': [],
        'Others': []
    }

    for ref in components:
        refs.add(ref)
        stats['Total Components'] += 1
        if ref.startswith('TP'):
            stats['Total TestPads'] += 1
            detailed_components['TestPads'].append(ref)
        elif ref.startswith('C'):
            stats['Total Capacitors'] += 1
            detailed_components['Capacitors'].append(ref)
        elif ref.startswith('R'):
            stats['Total Resistors'] += 1
            detailed_components['Resistors'].append(ref)
        elif ref.startswith('IC') or ref.startswith('U'):
            stats['Total ICs'] += 1
            detailed_components['ICs'].append(ref)
        elif ref.startswith('Q') or ref.startswith('T') or ref.startswith('FET'):
            # Ensure 'TP' is not included in FETs count
            if not ref.startswith('TP'):
                stats['Total FETs'] += 1
                detailed_components['FETs'].append(ref)
        elif ref.startswith('J') or ref.startswith('GPIO'):
            stats['Total Connectors'] += 1
            detailed_components['Connectors'].append(ref)
        elif ref.startswith('L'):
            stats['Total Inductors'] += 1
            detailed_components['Inductors'].append(ref)
        elif ref.startswith('MH') or ref.startswith('H'):
            stats['Total Mounting Holes'] += 1
            detailed_components['Mounting Holes'].append(ref)
        elif ref.startswith('FID'):
            stats['Total Fiducials'] += 1
            detailed_components['Fiducials'].append(ref)
        elif ref.startswith('D'):
            stats['Total Diodes/LEDs'] += 1
            detailed_components['Diodes/LEDs'].append(ref)
        elif ref.startswith('X'):
            stats['Total Crystals'] += 1
            detailed_components['Crystals'].append(ref)
        else:
            stats['Total Others'] += 1
            detailed_components['Others'].append(ref)

    stats['Total Refs'] = len(refs)
    return stats, detailed_components



def normalize_pinfunction(pinfunction):
    """Normalize pinfunction by stripping 'Pin_' if present at the start and if the remaining part is purely numeric."""
    if pinfunction.startswith('Pin_'):
        # Extract the remainder after 'Pin_' and check if it is purely numeric
        remainder = pinfunction[4:]
        if remainder.isdigit():  # Check if the remainder is a number
            return remainder
    return pinfunction


def generate_html_report(connections1, connections2, output_file, file1_name, file2_name, stats1, stats2, details1, details2):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')

    # Step 1: Create maps for netlist connections
    def create_connection_map(connections):
        connection_map = {}
        for net_name, net_connections in connections.items():
            for conn in net_connections:
                ref = conn[2]
                pin = conn[0]
                pinfunction = conn[1]
                key = (ref, pin)  # Simplify the key to only ref and pin
                if key not in connection_map:
                    connection_map[key] = {'net': net_name, 'details': []}
                connection_map[key]['details'].append({'pinfunction': pinfunction, 'net': net_name, 'details': conn})
        return connection_map

    connection_map1 = create_connection_map(connections1)
    connection_map2 = create_connection_map(connections2)

    mismatched_entries = []
    matched_entries = []

    # Step 2: Compare connections based on ref and pin
    for key, value1 in connection_map1.items():
        ref, pin = key

        # Check if ref starts with specific prefixes
        if ref.startswith(('U', 'IC', 'J', 'Q', 'X')):
            value2 = connection_map2.get(key)

            net1_name = value1['net'] if value1 else 'N/A'
            net2_name = value2['net'] if value2 else 'N/A'

            if value2:
                if net1_name == net2_name:
                    class_name = 'match'
                    pinfunction1 = next((d['pinfunction'] for d in value1['details']), 'N/A')
                    pinfunction2 = next((d['pinfunction'] for d in value2['details']), 'N/A')
                    matched_entries.append({
                        'pin1': pin,
                        'pinfunction1': pinfunction1,
                        'ref1': ref,
                        'net1_name': net1_name,
                        'pin2': pin,
                        'pinfunction2': pinfunction2,
                        'ref2': ref,
                        'net2_name': net2_name,
                        'class': class_name
                    })
                else:
                    class_name = 'mismatch'
                    pinfunction1 = next((d['pinfunction'] for d in value1['details']), 'N/A')
                    pinfunction2 = next((d['pinfunction'] for d in value2['details']), 'N/A')
                    mismatched_entries.append({
                        'pin1': pin,
                        'pinfunction1': pinfunction1,
                        'ref1': ref,
                        'net1_name': net1_name,
                        'pin2': pin,
                        'pinfunction2': pinfunction2,
                        'ref2': ref,
                        'net2_name': net2_name,
                        'class': class_name
                    })
            else:
                class_name = 'mismatch'
                pinfunction1 = next((d['pinfunction'] for d in value1['details']), 'N/A')
                mismatched_entries.append({
                    'pin1': pin,
                    'pinfunction1': pinfunction1,
                    'ref1': ref,
                    'net1_name': net1_name,
                    'pin2': pin,
                    'pinfunction2': 'N/A',
                    'ref2': ref,
                    'net2_name': 'N/A',
                    'class': class_name
                })

        else:
            # Handle cases where ref does not start with specific prefixes
            # Match based on ref and pin
            for net_name, net_connections in connections1.items():
                for conn in net_connections:
                    if conn[2] == ref and conn[0] == pin:
                        value2 = connection_map2.get((ref, pin))

                        net2_name = value2['net'] if value2 else 'N/A'
                        net1_name = net_name

                        if value2:
                            if net1_name == net2_name:
                                class_name = 'match'
                                pinfunction1 = conn[1]
                                pinfunction2 = next((d['pinfunction'] for d in value2['details']), 'N/A')
                                matched_entries.append({
                                    'pin1': pin,
                                    'pinfunction1': pinfunction1,
                                    'ref1': ref,
                                    'net1_name': net1_name,
                                    'pin2': pin,
                                    'pinfunction2': pinfunction2,
                                    'ref2': ref,
                                    'net2_name': net2_name,
                                    'class': class_name
                                })
                            else:
                                class_name = 'mismatch'
                                pinfunction1 = conn[1]
                                pinfunction2 = next((d['pinfunction'] for d in value2['details']), 'N/A')
                                mismatched_entries.append({
                                    'pin1': pin,
                                    'pinfunction1': pinfunction1,
                                    'ref1': ref,
                                    'net1_name': net1_name,
                                    'pin2': pin,
                                    'pinfunction2': pinfunction2,
                                    'ref2': ref,
                                    'net2_name': net2_name,
                                    'class': class_name
                                })
                        else:
                            class_name = 'mismatch'
                            pinfunction1 = conn[1]
                            mismatched_entries.append({
                                'pin1': pin,
                                'pinfunction1': pinfunction1,
                                'ref1': ref,
                                'net1_name': net1_name,
                                'pin2': pin,
                                'pinfunction2': 'N/A',
                                'ref2': ref,
                                'net2_name': 'N/A',
                                'class': class_name
                            })

    # Sort mismatched entries alphabetically by reference
    mismatched_entries.sort(key=lambda x: x['ref1'])
    # Sort matched entries alphabetically by reference
    matched_entries.sort(key=lambda x: x['ref1'])

    rows = mismatched_entries + matched_entries  # First mismatches, then matches

    total_mismatched = len(mismatched_entries)
    total_matched = len(matched_entries)

    with open(output_file, 'w') as file:
        file.write(template.render(
            file1_name=file1_name,
            file2_name=file2_name,
            data_rows=rows,
            total_capacitors1=stats1['Total Capacitors'],
            total_resistors1=stats1['Total Resistors'],
            total_ics1=stats1['Total ICs'],
            total_fets1=stats1['Total FETs'],
            total_connectors1=stats1['Total Connectors'],
            total_inductors1=stats1['Total Inductors'],
            total_mounting_holes1=stats1['Total Mounting Holes'],
            total_testpads1=stats1['Total TestPads'],
            total_fiducials1=stats1['Total Fiducials'],
            total_diodes_leds1=stats1['Total Diodes/LEDs'],
            total_crystals1=stats1['Total Crystals'],
            total_others1=stats1['Total Others'],
            total_refs1=stats1['Total Refs'],
            total_capacitors2=stats2['Total Capacitors'],
            total_resistors2=stats2['Total Resistors'],
            total_ics2=stats2['Total ICs'],
            total_fets2=stats2['Total FETs'],
            total_connectors2=stats2['Total Connectors'],
            total_inductors2=stats2['Total Inductors'],
            total_mounting_holes2=stats2['Total Mounting Holes'],
            total_testpads2=stats2['Total TestPads'],
            total_fiducials2=stats2['Total Fiducials'],
            total_diodes_leds2=stats2['Total Diodes/LEDs'],
            total_crystals2=stats2['Total Crystals'],
            total_others2=stats2['Total Others'],
            total_refs2=stats2['Total Refs'],
            capacitors1=details1['Capacitors'],
            resistors1=details1['Resistors'],
            ics1=details1['ICs'],
            fets1=details1['FETs'],
            connectors1=details1['Connectors'],
            inductors1=details1['Inductors'],
            mounting_holes1=details1['Mounting Holes'],
            testpads1=details1['TestPads'],
            fiducials1=details1['Fiducials'],
            diodes_leds1=details1['Diodes/LEDs'],
            crystals1=details1['Crystals'],
            others1=details1['Others'],
            capacitors2=details2['Capacitors'],
            resistors2=details2['Resistors'],
            ics2=details2['ICs'],
            fets2=details2['FETs'],
            connectors2=details2['Connectors'],
            inductors2=details2['Inductors'],
            mounting_holes2=details2['Mounting Holes'],
            testpads2=details2['TestPads'],
            fiducials2=details2['Fiducials'],
            diodes_leds2=details2['Diodes/LEDs'],
            crystals2=details2['Crystals'],
            others2=details2['Others'],
            total_mismatched=total_mismatched,
            total_matched=total_matched
        ))



def main():
    parser = argparse.ArgumentParser(description="Compare two KiCad netlist files.")
    parser.add_argument("file1", help="Path to the first KiCad netlist file.")
    parser.add_argument("file2", help="Path to the second KiCad netlist file.")
    parser.add_argument("output", help="Path to the output HTML file.")
    
    args = parser.parse_args()

    connections1, refs1, components1 = parse_netlist(args.file1)
    connections2, refs2, components2 = parse_netlist(args.file2)

    stats1, details1 = generate_stats(components1)
    stats2, details2 = generate_stats(components2)

    generate_html_report(connections1, connections2, args.output, args.file1, args.file2, stats1, stats2, details1, details2)


if __name__ == "__main__":
    main()
