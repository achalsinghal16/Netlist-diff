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
        in_components_section = False
        in_nets_section = False
        
        for line in lines:
            line = line.strip()  # Remove leading/trailing whitespace
            
            # Debug output
            #print(f"Processing line: {line}")

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
                    #print(f"Found net: {net_name}")
                    continue
            
            # Detect node connections
            if in_nets_section and line.startswith('(node'):
                node_match = re.match(r'\(node \(ref "(.*?)"\) \(pin "(.*?)"\)( \(pinfunction "(.*?)"\))?', line)
                if node_match:
                    ref = node_match.group(1)
                    pin = node_match.group(2)
                    pinfunction = node_match.group(4) if node_match.group(4) else ''
                    if net_name:
                        connections.setdefault(net_name, []).append((pin, pinfunction, ref))
                        refs.add(ref)
                        #print(f"Added node: (ref: {ref}, pin: {pin}, pinfunction: {pinfunction}) to net: {net_name}")
            
            # Detect component definitions
            if in_components_section and line.startswith('(comp'):
                comp_match = re.match(r'\(comp \(ref "(.*?)"\)', line)
                if comp_match:
                    ref = comp_match.group(1)
                    components[ref] = {}
                    #print(f"Found component: {ref}")
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
                continue

    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
    except Exception as e:
        print(f"Error: An unexpected error occurred while parsing {file_path} - {e}")
    
    #print(f"Connections parsed: {connections}")
    #print(f"References parsed: {refs}")
    #print(f"Components parsed: {components}")
    
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
            print(f"Skipping duplicate component: {ref}")
            continue
        
        processed_refs.add(ref)

        #print(f"Processing component: {ref} - {components[ref]}")
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



def print_component_counts(counts1, counts2):
    """Print the component counts for two netlists."""
    print("Component Counts for Netlist 1:")
    for key, value in counts1.items():
        print(f"{key}: {value}")
    
    print("\nComponent Counts for Netlist 2:")
    for key, value in counts2.items():
        print(f"{key}: {value}")


def generate_stats(components):
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
    
    for ref in components:
        refs.add(ref)
        stats['Total Components'] += 1
        if ref.startswith('C'):
            stats['Total Capacitors'] += 1
        elif ref.startswith('R'):
            stats['Total Resistors'] += 1
        elif ref.startswith('IC') or ref.startswith('U'):
            stats['Total ICs'] += 1
        elif ref.startswith('Q') or ref.startswith('T') or ref.startswith('FET'):
            stats['Total FETs'] += 1
        elif ref.startswith('J') or ref.startswith('GPIO'):
            stats['Total Connectors'] += 1
        elif ref.startswith('L'):
            stats['Total Inductors'] += 1
        elif ref.startswith('MH') or ref.startswith('H'):
            stats['Total Mounting Holes'] += 1
        elif ref.startswith('TP'):
            stats['Total TestPads'] += 1
            print(f"Debug: Found TestPad {ref}")  # Debug print
        elif ref.startswith('FID'):
            stats['Total Fiducials'] += 1
        elif ref.startswith('D'):
            stats['Total Diodes/LEDs'] += 1
        elif ref.startswith('X'):
            stats['Total Crystals'] += 1
        else:
            stats['Total Others'] += 1

    stats['Total Refs'] = len(refs)
    #print(stats)
    return stats



def generate_html_report(connections1, connections2, output_file, file1_name, file2_name, stats1, stats2):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template1.html')

    connection_map = {}

    def add_connections_to_map(connections, label):
        for net_name, net_connections in connections.items():
            for conn in net_connections:
                key = (conn[1], conn[2])
                if key not in connection_map:
                    connection_map[key] = {'net1': None, 'net2': None, 'details1': [], 'details2': [], 'refs1': [], 'refs2': []}
                connection_map[key][label] = net_name
                connection_map[key]['details' + label[-1]].append(conn)
                connection_map[key]['refs' + label[-1]].append(conn[2])

    add_connections_to_map(connections1, 'net1')
    add_connections_to_map(connections2, 'net2')

    rows = []

    for key, value in connection_map.items():
        pin, pinfunction = key
        net1_name = value['net1'] if value['net1'] else 'N/A'
        net2_name = value['net2'] if value['net2'] else 'N/A'
        refs1 = ', '.join(set(value['refs1'])) if value['refs1'] else 'N/A'
        refs2 = ', '.join(set(value['refs2'])) if value['refs2'] else 'N/A'

        row_class = 'match' if value['net1'] == value['net2'] else 'mismatch'

        rows.append({
            'class': row_class,
            'pin1': pin if value['net1'] else 'N/A',
            'pinfunction1': pinfunction if value['net1'] else 'N/A',
            'ref1': refs1,
            'net1_name': net1_name,
            'pin2': pin if value['net2'] else 'N/A',
            'pinfunction2': pinfunction if value['net2'] else 'N/A',
            'ref2': refs2,
            'net2_name': net2_name
        })

    rows.sort(key=lambda x: x['class'] == 'match', reverse=False)  # Sort with matches first

    # Debug print
    #print(f"Stats1: {stats1}")
    #print(f"Stats2: {stats2}")
    
    report = template.render(
        file1_name=file1_name,
        file2_name=file2_name,
        total_refs1=stats1['Total Refs'],
        total_refs2=stats2['Total Refs'],
        total_capacitors1=stats1['Total Capacitors'],
        total_capacitors2=stats2['Total Capacitors'],
        total_resistors1=stats1['Total Resistors'],
        total_resistors2=stats2['Total Resistors'],
        total_ics1=stats1['Total ICs'],
        total_ics2=stats2['Total ICs'],
        total_fets1=stats1['Total FETs'],
        total_fets2=stats2['Total FETs'],
        total_connectors1=stats1['Total Connectors'],
        total_connectors2=stats2['Total Connectors'],
        total_inductors1=stats1['Total Inductors'],
        total_inductors2=stats2['Total Inductors'],
        total_mounting_holes1=stats1['Total Mounting Holes'],
        total_mounting_holes2=stats2['Total Mounting Holes'],
        total_testpads1=stats1['Total TestPads'],
        total_testpads2=stats2['Total TestPads'],
        total_fiducials1=stats1['Total Fiducials'],
        total_fiducials2=stats2['Total Fiducials'],
        total_diodes_leds1=stats1['Total Diodes/LEDs'],
        total_diodes_leds2=stats2['Total Diodes/LEDs'],
        total_crystals1=stats1['Total Crystals'],
        total_crystals2=stats2['Total Crystals'],
        total_others1=stats1['Total Others'],
        total_others2=stats2['Total Others'],
        total_nets1=stats1['Total Nets'],
        total_nets2=stats2['Total Nets'],
        data_rows=rows
    )

    try:
        with open(output_file, 'w') as report_file:
            report_file.write(report)
    except Exception as e:
        print(f"Error: An unexpected error occurred while writing to {output_file} - {e}")
    else:
        print("HTML report generated successfully.")


def main():
    parser = argparse.ArgumentParser(description='Generate an HTML report comparing two KiCad netlists.')
    parser.add_argument('netlist1', type=str, help='Path to the first netlist file')
    parser.add_argument('netlist2', type=str, help='Path to the second netlist file')
    parser.add_argument('output', type=str, help='Path to the output HTML report file')

    args = parser.parse_args()

    connections1, refs1, components1 = parse_netlist(args.netlist1)
    connections2, refs2, components2 = parse_netlist(args.netlist2)

    counts1 = count_components(components1)
    counts2 = count_components(components2)

    stats1 = generate_stats(components1)
    stats2 = generate_stats(components2)

    print_component_counts(counts1, counts2)
    
    generate_html_report(connections1, connections2, args.output, args.netlist1, args.netlist2, stats1, stats2)

if __name__ == "__main__":
    main()
