import { useState, useEffect } from 'react';
import { openDB } from 'idb';

const DB_NAME = 'CatalogDB';
const STORE_NAME = 'automakers';

// Função auxiliar para configurar o IndexedDB
const initDB = async () => {
  return openDB(DB_NAME, 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    },
  });
};

export function useAutomakerCache() {
  const [automakers, setAutomakers] = useState<string[]>([]);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const fetchAndCache = async () => {
      try {
        const db = await initDB();
        
        // 1. Tenta pegar do cache local
        const cached = await db.get(STORE_NAME, 'list');
        const cacheTime = await db.get(STORE_NAME, 'timestamp');
        
        const now = new Date().getTime();
        // Recarrega se não tiver ou se tiver mais de 24 horas
        const isStale = !cacheTime || (now - cacheTime > 24 * 60 * 60 * 1000);

        if (cached && !isStale) {
          setAutomakers(cached);
          setIsReady(true);
          return;
        }

        // 2. Se offline ou precisar atualizar, busca da API
        const response = await fetch('http://localhost:8000/config/automakers');
        const data = await response.json();
        
        if (data.status === 'ok' && data.automakers) {
          // Acrescentamos as variáveis manuais para que o frontend entenda que GM e VW são marcas oficiais
          const extendedList = Array.from(new Set([...data.automakers, "GM", "VW"]));
          setAutomakers(extendedList);
          
          await db.put(STORE_NAME, extendedList, 'list');
          await db.put(STORE_NAME, now, 'timestamp');
        }
      } catch (error) {
        console.error('Erro ao buscar montadoras (FIPE):', error);
      } finally {
        setIsReady(true);
      }
    };

    fetchAndCache();
  }, []);

  return { automakers, isReady };
}
