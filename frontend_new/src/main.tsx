import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// StrictMode removido intencionalmente: o sistema é executado em modo dev e o StrictMode
// causava dupla montagem de todos os componentes, duplicando chamadas de API na inicialização
// e provocando "reload visual" da tela. Em produção não teria esse efeito, mas aqui impactava.
createRoot(document.getElementById('root')!).render(
  <App />
)
