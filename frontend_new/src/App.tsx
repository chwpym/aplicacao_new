import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Provedores from './pages/Provedores';
import Siglas from './pages/Siglas';
import Palavras from './pages/Palavras';
import Playground from './pages/Playground.tsx';
import Ajuda from './pages/Ajuda';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/provedores" element={<Provedores />} />
          <Route path="/siglas" element={<Siglas />} />
          <Route path="/palavras" element={<Palavras />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/ajuda" element={<Ajuda />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
