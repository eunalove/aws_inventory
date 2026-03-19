import pandas as pd
import requests
import json
import warnings
warnings.filterwarnings('ignore')

# ── 설정 ──────────────────────────────────────
AWX_URL           = "http://192.168.206.134:8013"
AWX_USER          = "admin"
AWX_PASSWORD      = "1234"
JOB_TEMPLATE_NAME = "방화벽 검사"

FIREWALL_EXCEL  = "firewall.xlsx"
INVENTORY_EXCEL = "inventory.xlsx"

# ── hostname → IP 매핑 ────────────────────────
def load_host_map():
    df = pd.read_excel(INVENTORY_EXCEL)
    return dict(zip(df['hostname'].astype(str).str.strip(),
                    df['ip'].astype(str).str.strip()))

# ── AWX Job Template ID 가져오기 ──────────────
def get_template_id():
    url = f"{AWX_URL}/api/v2/job_templates/"
    resp = requests.get(url, auth=(AWX_USER, AWX_PASSWORD), verify=False)
    for item in resp.json()['results']:
        if item['name'] == JOB_TEMPLATE_NAME:
            return item['id']
    raise Exception(f"Job Template '{JOB_TEMPLATE_NAME}' 찾을 수 없음")

# ── 메인 ──────────────────────────────────────
def main():
    host_map = load_host_map()

    df = pd.read_excel(FIREWALL_EXCEL)

    firewall_rules = []
    for _, row in df.iterrows():
        source = str(row['source']).strip()
        dest   = str(row['dest']).strip()
        port   = int(row['port'])

        # source는 반드시 인벤토리에 있어야 함
        if source not in host_map:
            print(f"❌ [{source}] 는 인벤토리에 등록되지 않은 호스트입니다.")
            print(f"   → inventory.xlsx에 {source}를 추가 후 다시 실행해주세요.")
            print()
            continue

        # dest는 hostname이면 IP로 변환, IP면 그대로 사용
        dest_ip = host_map.get(dest, dest)

        firewall_rules.append({
            "source_host": source,
            "target_ip"  : dest_ip,
            "target_port": port
        })

    if not firewall_rules:
        print("❌ 실행할 규칙이 없습니다. firewall.xlsx를 확인해주세요.")
        return

    print(f"\n총 {len(firewall_rules)}개 규칙:")
    for r in firewall_rules:
        print(f"  {r['source_host']} → {r['target_ip']}:{r['target_port']}")

    template_id = get_template_id()

    url = f"{AWX_URL}/api/v2/job_templates/{template_id}/launch/"
    payload = {
        "extra_vars": {
            "firewall_rules": firewall_rules
        }
    }
    resp = requests.post(
        url,
        auth=(AWX_USER, AWX_PASSWORD),
        json=payload,
        verify=False
    )

    print("응답 코드:", resp.status_code)
    print("응답 내용:", json.dumps(resp.json(), indent=2, ensure_ascii=False))

    job_id = resp.json().get('id')
    print(f"\n✅ Job #{job_id} 실행됨")
    print(f"AWX 확인: {AWX_URL}/#/jobs/{job_id}/output")

if __name__ == "__main__":
    main()