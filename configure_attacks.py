#!/usr/bin/env python3
"""
Attack Categories Configuration Script
Enable/disable specific attack types for automatic detection
"""

import sys
import json
import requests
from datetime import datetime
from attack_categories import AttackSubcategory, auto_detector

def show_available_categories():
    """Display all available attack categories"""
    print("🔧 Cyber Sentinel Attack Categories")
    print("=" * 50)
    
    categories = AttackSubcategory.get_all_categories()
    
    for i, category in enumerate(categories, 1):
        print(f"\n{i}. {category['category']}")
        for j, subcat in enumerate(category['subcategories'], 1):
            status = "✅" if subcat['id'] in auto_detector.enabled_attacks else "❌"
            print(f"   {j}.{status} {subcat['name']} ({subcat['severity']})")
            print(f"      {subcat['description']}")
            print(f"      Response: {subcat['auto_response']}")

def enable_critical_attacks():
    """Enable all critical severity attacks"""
    critical_attacks = []
    categories = AttackSubcategory.get_all_categories()
    
    for category in categories:
        for subcat in category['subcategories']:
            if subcat['severity'] == 'CRITICAL':
                critical_attacks.append(subcat['id'])
    
    auto_detector.enable_attack_detection(critical_attacks)
    print(f"✅ Enabled {len(critical_attacks)} critical attack types")

def enable_port_scans():
    """Enable all port scan detection"""
    port_scan_attacks = []
    categories = AttackSubcategory.get_all_categories()
    
    for category in categories:
        if category['category'] == 'Port Scan':
            for subcat in category['subcategories']:
                port_scan_attacks.append(subcat['id'])
    
    auto_detector.enable_attack_detection(port_scan_attacks)
    print(f"✅ Enabled {len(port_scan_attacks)} port scan types")

def enable_all_attacks():
    """Enable all attack types"""
    all_attacks = []
    categories = AttackSubcategory.get_all_categories()
    
    for category in categories:
        for subcat in category['subcategories']:
            all_attacks.append(subcat['id'])
    
    auto_detector.enable_attack_detection(all_attacks)
    print(f"✅ Enabled {len(all_attacks)} attack types")

def disable_all_attacks():
    """Disable all attack types"""
    enabled = list(auto_detector.enabled_attacks)
    auto_detector.disable_attack_detection(enabled)
    print(f"🚫 Disabled {len(enabled)} attack types")

def enable_specific_attacks(attack_ids):
    """Enable specific attack types by ID"""
    valid_attacks = []
    invalid_attacks = []
    
    for attack_id in attack_ids:
        info = AttackSubcategory.get_subcategory_info(attack_id)
        if info:
            valid_attacks.append(attack_id)
        else:
            invalid_attacks.append(attack_id)
    
    if invalid_attacks:
        print(f"❌ Invalid attack IDs: {invalid_attacks}")
        return False
    
    auto_detector.enable_attack_detection(valid_attacks)
    print(f"✅ Enabled {len(valid_attacks)} attack types")
    return True

def save_configuration():
    """Save current configuration to file"""
    config = {
        'enabled_attacks': list(auto_detector.enabled_attacks),
        'timestamp': str(datetime.now())
    }
    
    with open('attack_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("💾 Configuration saved to attack_config.json")

def load_configuration():
    """Load configuration from file"""
    try:
        with open('attack_config.json', 'r') as f:
            config = json.load(f)
        
        enabled = config.get('enabled_attacks', [])
        auto_detector.enable_attack_detection(enabled)
        print(f"📂 Loaded configuration with {len(enabled)} enabled attacks")
        return True
    except FileNotFoundError:
        print("❌ No saved configuration found")
        return False
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def show_status():
    """Show current detection status"""
    enabled = auto_detector.get_enabled_attacks()
    
    print(f"📊 Current Status:")
    print(f"   Enabled Attacks: {len(enabled)}")
    
    if enabled:
        print("   Active Categories:")
        categories = {}
        for attack in enabled:
            category = attack['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(attack['name'])
        
        for category, attacks in categories.items():
            print(f"     • {category}: {len(attacks)} attacks")
    else:
        print("   No attacks currently enabled")

def main():
    """Main configuration function"""
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print("Usage: python configure_attacks.py <command> [options]")
        print("\nCommands:")
        print("  show                    - Show all available categories")
        print("  status                  - Show current status")
        print("  critical                - Enable all critical attacks")
        print("  portscan                - Enable all port scans")
        print("  all                     - Enable all attacks")
        print("  none                    - Disable all attacks")
        print("  enable <attack_ids>     - Enable specific attacks")
        print("  save                    - Save current configuration")
        print("  load                    - Load saved configuration")
        print("\nExamples:")
        print("  python configure_attacks.py critical")
        print("  python configure_attacks.py enable SYN_SCAN NULL_SCAN")
        print("  python configure_attacks.py save")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'show':
        show_available_categories()
    elif command == 'status':
        show_status()
    elif command == 'critical':
        enable_critical_attacks()
        show_status()
    elif command == 'portscan':
        enable_port_scans()
        show_status()
    elif command == 'all':
        enable_all_attacks()
        show_status()
    elif command == 'none':
        disable_all_attacks()
        show_status()
    elif command == 'enable':
        if len(sys.argv) < 3:
            print("❌ Please provide attack IDs to enable")
            return
        attack_ids = sys.argv[2:]
        if enable_specific_attacks(attack_ids):
            show_status()
    elif command == 'save':
        save_configuration()
    elif command == 'load':
        load_configuration()
        show_status()
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == '__main__':
    main()
