/**
 * PlayerCard - Display player information in a card format
 */

import { Card, Tag, Space, Typography, Statistic, Row, Col } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import type { Player, PlayerInfo } from '../api/types';

const { Text } = Typography;

interface PlayerCardProps {
  player: Player | PlayerInfo;
  compact?: boolean;
  onClick?: () => void;
}

// Get color based on overall rating
function getOvrColor(ovr: number): string {
  if (ovr >= 90) return '#52c41a';  // green
  if (ovr >= 85) return '#1890ff';  // blue
  if (ovr >= 80) return '#722ed1';  // purple
  if (ovr >= 75) return '#faad14';  // gold
  return '#8c8c8c';  // gray
}

// Get position color
function getPositionColor(position: string): string {
  switch (position) {
    case 'FWD': return 'blue';
    case 'DEF': return 'green';
    case 'G': return 'orange';
    default: return 'default';
  }
}

export function PlayerCard({ player, compact = false, onClick }: PlayerCardProps) {
  const fullName = `${player.first_name} ${player.last_name}`;
  
  if (compact) {
    return (
      <Card 
        size="small" 
        hoverable={!!onClick}
        onClick={onClick}
        style={{ cursor: onClick ? 'pointer' : 'default' }}
      >
        <Space>
          <Tag color={getPositionColor(player.position)}>{player.position}</Tag>
          <Text strong>{fullName}</Text>
          <Tag color={getOvrColor(player.overall)}>{player.overall} OVR</Tag>
          <Text type="secondary">{player.team}</Text>
        </Space>
      </Card>
    );
  }

  return (
    <Card
      hoverable={!!onClick}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
      title={
        <Space>
          <UserOutlined />
          <span>{fullName}</span>
          <Tag color={getPositionColor(player.position)}>{player.position}</Tag>
        </Space>
      }
      extra={
        <Tag color={getOvrColor(player.overall)} style={{ fontSize: 16, padding: '4px 12px' }}>
          {player.overall} OVR
        </Tag>
      }
    >
      <Row gutter={16}>
        <Col span={8}>
          <Statistic title="Salary" value={player.salary} suffix="K" />
        </Col>
        <Col span={8}>
          <Statistic title="Team" value={player.team} />
        </Col>
        <Col span={8}>
          <Statistic title="Nationality" value={player.nationality} />
        </Col>
      </Row>
      {'event' in player && player.event && (
        <div style={{ marginTop: 12 }}>
          <Tag color="purple">{player.event}</Tag>
        </div>
      )}
    </Card>
  );
}

export default PlayerCard;
