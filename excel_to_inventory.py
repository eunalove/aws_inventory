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

        # 1. pull 전에 로컬 변경사항 stash (hosts.yml 포함)
        subprocess.run(['git', 'stash'], check=True)

        # 2. 원격 최신 반영
        subprocess.run(['git', 'pull', 'origin', 'main'], check=True)

        # 3. stash 복원 (충돌 시 에러로 잡힘)
        result = subprocess.run(['git', 'stash', 'pop'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️  stash pop 충돌 발생, 강제로 hosts.yml 덮어씁니다.\n{result.stderr}")
            # 충돌 시 생성한 hosts.yml을 다시 덮어쓰기
            excel_to_yaml()

        # 4. 변경사항 없으면 커밋 스킵
        diff = subprocess.run(['git', 'diff', '--cached', '--quiet', OUTPUT_FILE],
                              capture_output=True)
        subprocess.run(['git', 'add', OUTPUT_FILE], check=True)

        diff_after_add = subprocess.run(['git', 'diff', '--cached', '--quiet'],
                                        capture_output=True)
        if diff_after_add.returncode == 0:
            print("ℹ️  변경사항 없음, 커밋 스킵")
            return

        subprocess.run(['git', 'commit', '-m', 'Auto: inventory update'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Git push 완료")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git 오류: {e}")


if __name__ == "__main__":
    if excel_to_yaml():
        git_push()