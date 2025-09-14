# src/data_loader.py
import os
import io
import zipfile
import pandas as pd

def try_read_csv_bytes(content, encodings=('utf-8','cp1251','windows-1251')):
    for enc in encodings:
        try:
            return pd.read_csv(io.BytesIO(content), encoding=enc)
        except Exception:
            continue
    return pd.read_csv(io.BytesIO(content), low_memory=False)

def load_zip_by_client(zip_path):
    """
    Читает zip файл, содержащий множество csv (transactions и transfers для клиентов).
    Возвращает dict: clients[client_code] = {'transactions': df, 'transfers': df}
    """
    z = zipfile.ZipFile(zip_path)
    clients = {}
    for name in z.namelist():
        if name.endswith('/') or name.startswith('__MACOSX'):
            continue
        content = z.read(name)
        try:
            df = try_read_csv_bytes(content)
        except Exception as e:
            print(f"Couldn't read {name}: {e}")
            continue
        # Убедимся, что есть client_code
        cols_lower = [c.lower().strip() for c in df.columns]
        df.columns = [c.strip() for c in df.columns]
        if 'client_code' not in df.columns and 'client_code' not in cols_lower:
            # попробуем извлечь id из имени файла
            import re
            m = re.search(r'(\d+)', name)
            if m:
                df['client_code'] = int(m.group(1))
            else:
                # пропускаем файл без client_code
                continue
        # стандартизируем имена колонок на нижний регистр
        df.columns = [c.lower() for c in df.columns]
        # определяем тип файла
        if 'category' in df.columns:
            ftype = 'transactions'
        elif 'type' in df.columns and 'direction' in df.columns:
            ftype = 'transfers'
        else:
            # если неясно, постараемся угадать
            if 'amount' in df.columns and 'date' in df.columns and 'category' in df.columns:
                ftype = 'transactions'
            elif 'amount' in df.columns and 'direction' in df.columns:
                ftype = 'transfers'
            else:
                ftype = 'other'
        # группируем по client_code
        for cid in df['client_code'].unique():
            sub = df[df['client_code']==cid].copy()
            if cid not in clients:
                clients[cid] = {}
            if ftype in clients[cid]:
                clients[cid][ftype] = pd.concat([clients[cid][ftype], sub], ignore_index=True)
            else:
                clients[cid][ftype] = sub
    return clients

def load_csv_list(file_paths):
    """
    Альтернатива: если передан список csv-файлов уже распакованных.
    Ожидается, что имена файлов содержат client_code или файлы имеют колонку client_code.
    Возвращает clients dict аналогично load_zip_by_client.
    """
    clients = {}
    for path in file_paths:
        try:
            df = pd.read_csv(path)
        except Exception:
            df = pd.read_csv(path, encoding='cp1251', low_memory=False)
        df.columns = [c.lower().strip() for c in df.columns]
        if 'client_code' not in df.columns:
            import re
            m = re.search(r'(\d+)', os.path.basename(path))
            if m:
                df['client_code'] = int(m.group(1))
            else:
                continue
        if 'category' in df.columns:
            ftype = 'transactions'
        elif 'type' in df.columns and 'direction' in df.columns:
            ftype = 'transfers'
        else:
            ftype = 'other'
        for cid in df['client_code'].unique():
            sub = df[df['client_code']==cid].copy()
            if cid not in clients:
                clients[cid] = {}
            if ftype in clients[cid]:
                clients[cid][ftype] = pd.concat([clients[cid][ftype], sub], ignore_index=True)
            else:
                clients[cid][ftype] = sub
    return clients
