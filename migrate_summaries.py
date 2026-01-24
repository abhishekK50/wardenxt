"""
Migration Script: Add Missing Fields to summary.json Files
Enriches existing incident summaries with fields needed by frontend
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

# Mapping of incident IDs to their types
INCIDENT_TYPES = {
    "INC-2026-0001": "bmr_recovery",
    "INC-2026-0002": "connection_pool_exhaustion",
    "INC-2026-0003": "memory_leak",
    "INC-2026-0004": "dns_propagation",
    "INC-2026-0005": "kubernetes_crashloop"
}

def migrate_summary(summary_path: Path, incident_id: str):
    """Migrate a single summary.json file"""
    
    print(f"Migrating {incident_id}...")
    
    # Load existing summary
    with open(summary_path, 'r') as f:
        data = json.load(f)
    
    # Add incident_type if missing
    if 'incident_type' not in data:
        data['incident_type'] = INCIDENT_TYPES.get(incident_id, 'unknown')
    
    # Calculate timestamps based on duration
    duration_minutes = data.get('duration_minutes', 0)
    
    if 'start_time' not in data:
        # Use a realistic timestamp (2 days ago at 2 AM)
        start_time = datetime.now() - timedelta(days=2, hours=-2)
        data['start_time'] = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
    
    if 'end_time' not in data:
        end_time = start_time + timedelta(minutes=duration_minutes)
        data['end_time'] = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    if 'detection_time' not in data:
        # Detection 2 minutes after start
        detection_time = start_time + timedelta(minutes=2)
        data['detection_time'] = detection_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    if 'resolution_time' not in data:
        resolution_time = start_time + timedelta(minutes=duration_minutes)
        data['resolution_time'] = resolution_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Add business impact if missing
    if 'business_impact' not in data:
        severity = data.get('severity', 'P2')
        if severity == 'P0':
            data['business_impact'] = 'CRITICAL - Complete service outage'
        elif severity == 'P1':
            data['business_impact'] = 'HIGH - Major service degradation'
        elif severity == 'P2':
            data['business_impact'] = 'MEDIUM - Partial service impact'
        else:
            data['business_impact'] = 'LOW - Minimal impact'
    
    # Add MTTR fields if missing
    if 'mttr_actual' not in data:
        hours = duration_minutes // 60
        mins = duration_minutes % 60
        data['mttr_actual'] = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
    
    if 'mttr_target' not in data:
        # Target is typically 50% of actual for P1/P2
        target_minutes = duration_minutes // 2
        hours = target_minutes // 60
        mins = target_minutes % 60
        data['mttr_target'] = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
    
    # Backup original file
    backup_path = summary_path.parent / 'summary.json.bak'
    with open(summary_path, 'r') as f:
        backup_data = json.load(f)
    with open(backup_path, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    # Write migrated summary
    with open(summary_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Migrated {incident_id}")
    print(f"  - Added incident_type: {data['incident_type']}")
    print(f"  - Added timestamps: {data['start_time']} to {data['end_time']}")
    print(f"  - Backup saved to: summary.json.bak")


def main():
    """Migrate all summary files"""
    
    # Get data directory - script should be in project root
    script_dir = Path(__file__).parent.resolve()
    data_dir = script_dir / 'data-generation' / 'output'
    
    print(f"Script location: {script_dir}")
    print(f"Looking for incidents in: {data_dir}")
    print("=" * 60)
    
    if not data_dir.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        print("\nPlease make sure:")
        print("1. This script is in the project root (wardenxt/)")
        print("2. data-generation/output/ exists with incident folders")
        print("\nCurrent directory structure should be:")
        print("wardenxt/")
        print("├── migrate_summaries.py  (this script)")
        print("├── backend/")
        print("├── frontend/")
        print("└── data-generation/")
        print("    └── output/")
        print("        ├── INC-2026-0001/")
        print("        ├── INC-2026-0002/")
        print("        └── ...")
        return
    
    # Find all incident directories
    incident_dirs = [
        d for d in data_dir.iterdir() 
        if d.is_dir() and (d / 'summary.json').exists()
    ]
    
    if not incident_dirs:
        print(f"ERROR: No incident directories found in {data_dir}")
        print("\nMake sure each incident has a summary.json file:")
        print("- INC-2026-0001/summary.json")
        print("- INC-2026-0002/summary.json")
        print("- etc.")
        return
    
    print(f"Found {len(incident_dirs)} incidents to migrate\n")
    
    # Migrate each incident
    success_count = 0
    error_count = 0
    
    for incident_dir in sorted(incident_dirs):
        incident_id = incident_dir.name
        summary_path = incident_dir / 'summary.json'
        
        try:
            migrate_summary(summary_path, incident_id)
            success_count += 1
            print()  # Empty line for readability
        except Exception as e:
            print(f"✗ Error migrating {incident_id}: {e}")
            error_count += 1
            print()
    
    print("=" * 60)
    print(f"Migration complete!")
    print(f"  ✓ Successfully migrated: {success_count}")
    if error_count > 0:
        print(f"  ✗ Errors: {error_count}")
    
    print("\nNext steps:")
    print("1. Restart your backend server:")
    print("   cd backend")
    print("   .\\venv\\Scripts\\Activate.ps1")
    print("   python -m app.main")
    print("2. Test: http://localhost:8000/api/incidents/")
    print("3. Check frontend dashboard at http://localhost:3000")


if __name__ == '__main__':
    main()