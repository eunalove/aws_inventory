import pandas as pd
import yaml
import subprocess
import os

EXCEL_FILE = "inventory.xlsx"
OUTPUT_FILE = "inventories/hosts.yml"
REPO_PATH = os.path.dirname(os.path.abspath(__file__))

def excel_to_yaml():
    df = pd.read_excel(EXCEL_FILE)
    df = df[df['enabled'].str.upper() == 'Y']
    
    inventory = {'all': {'children': {}}}
    
    for _, row in df.iterrows():
        group = row['group']
        hostname = row['hostname']
        
        if group not in inventory['all']['children']:
            inventory['all']['children'][group] = {'hosts': {}}
        
        inventory['all']['children'][group]['hosts'][hostname] = {
            'ansible_host': str(row['ip']),
            'ansible_port': int(row['port']),
            'ansible_user': str(row['ansible_user'])
        }
    
    os.makedirs('inventories', exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        yaml.dump(inventory, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ {OUTPUT_FILE} 생성 완료")
    return True

def git_push():
    try:
        os.chdir(REPO_PATH)
        subprocess.run(['git', 'pull', 'origin', 'main'], check=True)  # 추가
        subprocess.run(['git', 'add', OUTPUT_FILE], check=True)
        subprocess.run(['git', 'commit', '-m', 'Auto: inventory update'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Git push 완료")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 오류: {e}")

if __name__ == "__main__":
    if excel_to_yaml():
        git_push()
