from dotenv import load_dotenv
from context import load_data
from port_client import PortClient

def main():
    load_dotenv()
    client=PortClient()
    client.create_blueprint()
    services,_,_=load_data()
    for s in services:
        client.upsert_service(s)
        print('Uploaded:',s['identifier'])
    print('Done. Seeded',len(services),'services into contextcost_service.')

if __name__=='__main__':main()
