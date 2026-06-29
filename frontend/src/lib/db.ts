export const initDB = (): Promise<IDBDatabase> => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('SuperRagDB', 1);
    
    request.onupgradeneeded = (event: any) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('files')) {
        db.createObjectStore('files', { keyPath: 'name' });
      }
    };
    
    request.onsuccess = (event: any) => resolve(event.target.result);
    request.onerror = (event: any) => reject(event.target.error);
  });
};

export const saveFileToLocal = async (file: File) => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction('files', 'readwrite');
    const store = transaction.objectStore('files');
    const request = store.put({ name: file.name, file: file });
    
    request.onsuccess = () => resolve(true);
    request.onerror = () => reject(false);
  });
};

export const getLocalFiles = async (): Promise<File[]> => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction('files', 'readonly');
    const store = transaction.objectStore('files');
    const request = store.getAll();
    
    request.onsuccess = (event: any) => {
      resolve(event.target.result.map((item: any) => item.file));
    };
    request.onerror = () => reject([]);
  });
};

export const deleteLocalFile = async (name: string) => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction('files', 'readwrite');
    const store = transaction.objectStore('files');
    const request = store.delete(name);
    
    request.onsuccess = () => resolve(true);
    request.onerror = () => reject(false);
  });
};
