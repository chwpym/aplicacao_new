import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000', // Porta padrão do FastAPI / Uvicorn
});

export const searchApi = {
    buscarPeca: (id: string, provedorIds?: number[], agrupar = true, config: any = {}) => {
        const params: any = { agrupar };
        if (provedorIds) params.provedores = provedorIds.join(',');
        return api.get(`/search/${encodeURIComponent(id)}`, { ...config, params });
    },
    getDetalhesPeca: (codigo: string, provedorId: number) => {
        return api.get(`/search/details/peca`, { params: { codigo, provedor_id: provedorId } });
    }
};

export const configApi = {
    getProvedores: () => api.get('/config/provedores'),
    createProvedor: (data: any) => api.post('/config/provedores', data),
    updateProvedor: (id: number, data: any) => api.put(`/config/provedores/${id}`, data),
    deleteProvedor: (id: number) => api.delete(`/config/provedores/${id}`),

    getSiglas: () => api.get('/config/siglas'),
    createSigla: (data: any) => api.post('/config/siglas', data),
    deleteSigla: (id: number) => api.delete(`/config/siglas/${id}`),

    getPalavras: () => api.get('/config/palavras'),
    createPalavra: (data: any) => api.post('/config/palavras', data),
    deletePalavra: (id: number) => api.delete(`/config/palavras/${id}`),

    getHealth: () => api.get('/api/health'),
    exportBackup: () => api.post('/config/backup/export'),
};

export default api;
