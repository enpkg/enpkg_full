import hashlib

def get_hash(f_path, mode='md5'):
    h = hashlib.new(mode)
    with open(f_path, 'rb') as file:
        data = file.read()
        file.close()
    h.update(data)
    digest = h.hexdigest()
    return digest

def get_data(f_path):
    with open(f_path, 'r') as file:
        data = file.read()
        file.close()
    return data