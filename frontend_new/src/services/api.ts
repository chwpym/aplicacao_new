import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000', // Porta padrão do FastAPI / Uvicorn
});

export const searchApi = {
    buscarPeca: (id: string, provedorIds?: number[], agrupar = true) => {
        const params: any = { agrupar };
        if (provedorIds) params.provedores = provedorIds.join(',');
        return api.get(`/search/${encodeURIComponent(id)}`, { params });
    },
    testarProvedor: (idPeca: string, config: any) => {
        return api.post('/search/test', { id_peca: idPeca, config });
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
};

export default api;
