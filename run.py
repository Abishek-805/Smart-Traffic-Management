"""Launch the combined local app without Redis or bundled demo video dependencies."""
import os
os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
os.environ.setdefault("KMP_BLOCKTIME", "0")
import argparse
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

if __name__ == '__main__':
    load_dotenv(Path(__file__).parent / '.env')
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    import os
    os.environ.setdefault('CAMERA_WS_PORT', str(args.port))
    uvicorn.run('web.app:app', host=args.host, port=args.port)
