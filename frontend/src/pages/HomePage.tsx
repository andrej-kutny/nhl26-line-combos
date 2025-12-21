/**
 * HomePage - Dashboard with statistics
 */

import { Row, Col, Card, Statistic, Typography, Flex, Space, Button, Alert } from 'antd';
import {
  UserOutlined,
  TeamOutlined,
  TrophyOutlined,
  RocketOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { getStats } from '../api/players';

const { Title, Paragraph } = Typography;

export function HomePage() {
  const { data: stats, loading, error } = useApi(() => getStats(), []);

  return (
    <Flex vertical gap="large" style={{ width: '100%' }}>
      <div>
        <Title level={2}>NHL 26 Line Combos Optimizer</Title>
        <Paragraph type="secondary">
          Find optimal NHL 26 HUT line combinations using Answer Set Programming (ASP) with Clingo.
        </Paragraph>
      </div>

      {error && (
        <Alert
          title="Failed to load statistics"
          description={error}
          type="error"
          showIcon
        />
      )}

      {/* Statistics Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card loading={loading}>
            <Statistic
              title="Forwards"
              value={stats?.players?.forwards || 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card loading={loading}>
            <Statistic
              title="Defense"
              value={stats?.players?.defense || 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card loading={loading}>
            <Statistic
              title="Goalies"
              value={stats?.players?.goalies || 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card loading={loading}>
            <Statistic
              title="Forward Combos"
              value={stats?.combos?.forward_combos || 0}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card loading={loading}>
            <Statistic
              title="Defense Combos"
              value={stats?.combos?.defense_combos || 0}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card loading={loading}>
            <Statistic
              title="Teams"
              value={stats?.teams?.length || 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Card title="Quick Actions">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Link to="/players">
              <Button type="primary" icon={<SearchOutlined />} block size="large">
                Browse Players
              </Button>
            </Link>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Link to="/optimize">
              <Button type="default" icon={<RocketOutlined />} block size="large">
                Optimize Lines
              </Button>
            </Link>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Link to="/best">
              <Button type="default" icon={<TrophyOutlined />} block size="large">
                View Best Lines
              </Button>
            </Link>
          </Col>
        </Row>
      </Card>

      {/* Project Info */}
      <Card title="About">
        <Paragraph>
          This project is part of the <strong>TKRR25 Knowledge Representation and Reasoning</strong> course 
          final project at Jönköping University.
        </Paragraph>
        <Paragraph>
          <strong>Key Technologies:</strong>
        </Paragraph>
        <Space wrap>
          <span>Clingo (ASP)</span>
          <span>•</span>
          <span>FastAPI</span>
          <span>•</span>
          <span>React</span>
          <span>•</span>
          <span>Ant Design</span>
          <span>•</span>
          <span>SQLite</span>
        </Space>
      </Card>
    </Flex>
  );
}

export default HomePage;
