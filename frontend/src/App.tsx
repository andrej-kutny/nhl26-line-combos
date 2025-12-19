import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu, Typography, Card, Space, Button } from 'antd';
import {
  HomeOutlined,
  UserOutlined,
  TrophyOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph } = Typography;

// Placeholder pages - will be implemented in Phase 2
function HomePage() {
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={2}>NHL 26 Line Combos Optimizer</Title>
      <Card title="Welcome">
        <Paragraph>
          Find optimal NHL 26 HUT line combinations using Answer Set Programming (ASP) with Clingo.
        </Paragraph>
        <Space>
          <Button type="primary">
            <Link to="/players">Browse Players</Link>
          </Button>
          <Button>
            <Link to="/optimize">Optimize Lines</Link>
          </Button>
        </Space>
      </Card>
    </Space>
  );
}

function PlayersPage() {
  return (
    <Card title="Players">
      <Paragraph>Player browser will be implemented here.</Paragraph>
    </Card>
  );
}

function OptimizePage() {
  return (
    <Card title="Optimize Lines">
      <Paragraph>Line optimization form will be implemented here.</Paragraph>
    </Card>
  );
}

function BestLinesPage() {
  return (
    <Card title="Best Lines (Goal 1 Results)">
      <Paragraph>Best line combinations will be displayed here.</Paragraph>
    </Card>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ color: 'white', fontWeight: 'bold', marginRight: 24 }}>
            NHL26 Line Combos
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            defaultSelectedKeys={['home']}
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
                icon: <SettingOutlined />,
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
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/players" element={<PlayersPage />} />
            <Route path="/optimize" element={<OptimizePage />} />
            <Route path="/best" element={<BestLinesPage />} />
          </Routes>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          NHL 26 Line Combos Optimizer - KRR Final Project - Jönköping University
        </Footer>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
