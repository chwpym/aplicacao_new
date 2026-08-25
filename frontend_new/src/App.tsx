import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import HomeTable from './pages/HomeTable';
import Provedores from './pages/Provedores';
import Siglas from './pages/Siglas';
import Palavras from './pages/Palavras';
import Playground from './pages/Playground.tsx';
import Ajuda from './pages/Ajuda';
import Configuracoes from './pages/Configuracoes';
import ManualProvedores from './pages/ManualProvedores';
import Documentacao from './pages/Documentacao';
import Automakers from './pages/Automakers';
import DesignPreview from './pages/DesignPreview';
import { Etiquetas } from "./pages/Etiquetas";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/catalogo" replace />} />
          <Route path="/catalogo" element={<Home />} />
          <Route path="/table-test" element={<HomeTable />} />
          <Route path="/etiquetas" element={<Etiquetas />} />
          <Route path="/provedores" element={<Provedores />} />
          <Route path="/siglas" element={<Siglas />} />
          <Route path="/palavras" element={<Palavras />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/automakers" element={<Automakers />} />
          <Route path="/design-preview" element={<DesignPreview />} />
          <Route path="/ajuda" element={<Ajuda />} />
          <Route path="/manual-provedores" element={<ManualProvedores />} />
          <Route path="/documentacao" element={<Documentacao />} />
          <Route path="/configuracoes" element={<Configuracoes />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
