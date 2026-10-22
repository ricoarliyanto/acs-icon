#!/usr/bin/env python3
"""
Auto-generate CWMP dialect for UGRID ONT
Based on datamodel CSV and Huawei reference pattern
"""
import csv
import os
from collections import defaultdict

# Paths
UGRID_DATAMODEL = '/home/win/code/acs-icon/datamodel/ugrid/4C3FA731AFD5_datamodel.csv'
HUAWEI_DIALECT = '/home/win/code/acs-icon/Device_dialects/cwmp/devices/huawei/EG8041V5-rev2'
OUTPUT_DIR = '/home/win/code/acs-icon/Device_dialects/cwmp/devices/ugrid'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'ugrid-ont-rev1')

def read_huawei_dialect():
    """Read Huawei dialect as reference structure"""
    if not os.path.exists(HUAWEI_DIALECT):
        print(f"⚠️  Huawei dialect not found: {HUAWEI_DIALECT}")
        return {}
    
    params = {}
    with open(HUAWEI_DIALECT, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(';')
                if len(parts) >= 4:
                    name = parts[0]
                    params[name] = {
                        'type': parts[1] if len(parts) > 1 else '',
                        'access': parts[2] if len(parts) > 2 else '',
                        'writable': parts[3] if len(parts) > 3 else 'false'
                    }
    print(f"✅ Loaded {len(params)} parameters from Huawei dialect")
    return params

def read_ugrid_datamodel():
    """Read UGRID datamodel CSV"""
    if not os.path.exists(UGRID_DATAMODEL):
        print(f" UGRID datamodel not found: {UGRID_DATAMODEL}")
        return []
    
    params = []
    with open(UGRID_DATAMODEL, 'r') as f:
        # Try to detect delimiter
        first_line = f.readline()
        f.seek(0)
        
        if ';' in first_line:
            delimiter = ';'
        elif ',' in first_line:
            delimiter = ','
        else:
            delimiter = '\t'
        
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if len(row) >= 2:
                param_name = row[0].strip()
                
                # Skip comments and empty lines
                if not param_name or param_name.startswith('#'):
                    continue
                
                param_type = row[1].strip() if len(row) > 1 else 'xsd:string'
                access = row[2].strip() if len(row) > 2 else ''
                writable = row[3].strip().lower() if len(row) > 3 else 'false'
                
                params.append({
                    'name': param_name,
                    'type': param_type,
                    'access': access,
                    'writable': writable == 'true'
                })
    
    print(f"✅ Loaded {len(params)} parameters from UGRID datamodel")
    return params

def group_parameters(params):
    """Group parameters by top-level object"""
    groups = defaultdict(list)
    for param in params:
        parts = param['name'].split('.')
        if len(parts) >= 2:
            # Group by first 2-3 parts (e.g., InternetGatewayDevice.DeviceInfo)
            if len(parts) >= 3:
                group = parts[0] + '.' + parts[1]
            else:
                group = parts[0]
            groups[group].append(param)
    return groups

def generate_dialect(ugrid_params, huawei_params):
    """Generate CWMP dialect file"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Group UGRID parameters
    groups = group_parameters(ugrid_params)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write("# UGRID ONT CWMP Dialect\n")
        f.write("# Auto-generated from datamodel 4C3FA731AFD5\n")
        f.write("# Reference: Huawei EG8041V5 dialect pattern\n\n")
        
        total_params = 0
        for group_name, params in sorted(groups.items()):
            f.write(f"# {'='*60}\n")
            f.write(f"# {group_name}\n")
            f.write(f"# {'='*60}\n\n")
            
            for param in sorted(params, key=lambda x: x['name']):
                name = param['name']
                ptype = param['type']
                access = param['access']
                writable = 'true' if param['writable'] else 'false'
                
                # Format: name;type;access;writable;
                f.write(f"{name};{ptype};{access};{writable};\n")
                total_params += 1
            
            f.write("\n")
        
        f.write(f"# Total: {total_params} parameters in {len(groups)} groups\n")
    
    return total_params, len(groups)

def main():
    print("🔧 UGRID CWMP Dialect Generator")
    print("="*60)
    
    # Read reference
    huawei_params = read_huawei_dialect()
    
    # Read UGRID datamodel
    ugrid_params = read_ugrid_datamodel()
    
    if not ugrid_params:
        print("❌ No parameters found in UGRID datamodel")
        return
    
    # Generate dialect
    total_params, total_groups = generate_dialect(ugrid_params, huawei_params)
    
    print("="*60)
    print(f"✅ Dialect generated successfully!")
    print(f"📁 Output: {OUTPUT_FILE}")
    print(f"📊 Stats: {total_params} parameters in {total_groups} groups")
    print(f"💡 Next: Review and adjust manually if needed")
    print("="*60)

if __name__ == '__main__':
    main()
