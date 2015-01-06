from app.Deployer import Deployer

# init: check and load configuration
worker = Deployer()

# clone and fetch / pull
worker.sync_repositories()

print('Done. Check your dump path.')