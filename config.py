# Dryrun
endpoint_dryrun = 'https://paper-api.alpaca.markets'
key_id_dryrun = 'PKIHRBOYBALCQKEEBQAJ'
secret_key_dryrun = 'drkNL1YqNjYkZ9ml0AJHlURDARX7iglitKcPXqxk'

# live accounts
endpoint = 'https://api.alpaca.markets'
key_id = 'AKQ8FW4G4MN713R1FND2'
secret_key = 'H2qzQ4JlgZknGlA727OMnZflKDz3HpsPIidmbQ5j'

# DB connection
db_path = '/Users/malojust/PycharmProjects/FS-Jware-Trading/FS_Jware_Trading.db'


def get_keys(request='endpoint', dryrun=True):
    if dryrun:
        if request == 'key_id':
            return key_id_dryrun
        elif request == 'secret_key':
            return secret_key_dryrun
        else:
            return endpoint_dryrun
    else:
        if request == 'key_id':
            return key_id
        elif request == 'secret_key':
            return secret_key
        else:
            return endpoint
