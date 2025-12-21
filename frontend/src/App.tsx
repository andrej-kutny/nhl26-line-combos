import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  HomeOutlined,
  UserOutlined,
  TrophyOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import { HomePage, PlayersPage, OptimizePage, BestLinesPage } from './pages';

const { Header, Content, Footer } = Layout;

function AppLayout() {
  const location = useLocation();

  // Determine selected menu key based on current path
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path === '/') return 'home';
    if (path.startsWith('/players')) return 'players';
    if (path.startsWith('/optimize')) return 'optimize';
    if (path.startsWith('/best')) return 'best';
    return 'home';
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <div style={{ color: 'white', fontWeight: 'bold', marginRight: 32, fontSize: 16 }}>
          NHL26 Line Combos
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[getSelectedKey()]}
          items={[
            {
              key: 'home',
              icon: <HomeOutlined />,
              label: <Link to="/">Home</Link>,
            },
            {
              key: 'players',
              icon: <UserOutlined />,
              label: <Link to="/players">Players</Link>,
            },
            {
              key: 'optimize',
              icon: <RocketOutlined />,
              label: <Link to="/optimize">Optimize</Link>,
            },
            {
              key: 'best',
              icon: <TrophyOutlined />,
              label: <Link to="/best">Best Lines</Link>,
            },
          ]}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Content style={{ padding: '24px 48px' }}>
        <div style={{ background: '#fff', padding: 24, minHeight: 280, borderRadius: 8 }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/players" element={<PlayersPage />} />
            <Route path="/optimize" element={<OptimizePage />} />
            <Route path="/best" element={<BestLinesPage />} />
          </Routes>
        </div>
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        NHL 26 Line Combos Optimizer - KRR Final Project - Jönköping University
      </Footer>
    </Layout>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}

export default App;
