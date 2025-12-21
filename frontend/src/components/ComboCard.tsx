/**
 * ComboCard - Display a line combination with its conditions and rewards
 */

import { Card, Tag, Space, Typography, Flex } from 'antd';
import { GiftOutlined, TeamOutlined, GlobalOutlined, CalendarOutlined } from '@ant-design/icons';
import type { LineCombo, ComboCondition } from '../api/types';

const { Text } = Typography;

interface ComboCardProps {
  combo: LineCombo;
  onClick?: () => void;
}

// Get icon for condition type
function getConditionIcon(type: string) {
  switch (type) {
    case 'team': return <TeamOutlined />;
    case 'nationality': return <GlobalOutlined />;
    case 'event': return <CalendarOutlined />;
    default: return null;
  }
}

// Get color for reward type
function getRewardColor(type: string): string {
  switch (type) {
    case 'OVR': return 'green';
    case 'SAL': return 'blue';
    case 'AP': return 'purple';
    default: return 'default';
  }
}

// Get condition tag color
function getConditionColor(type: string): string {
  switch (type) {
    case 'team': return 'cyan';
    case 'nationality': return 'magenta';
    case 'event': return 'orange';
    default: return 'default';
  }
}

function ConditionTag({ condition }: { condition: ComboCondition }) {
  return (
    <Tag color={getConditionColor(condition.type)} icon={getConditionIcon(condition.type)}>
      {condition.type}: {condition.key}
    </Tag>
  );
}

export function ComboCard({ combo, onClick }: ComboCardProps) {
  const conditions = [combo.condition1, combo.condition2];
  if (combo.condition3) {
    conditions.push(combo.condition3);
  }

  return (
    <Card
      size="small"
      hoverable={!!onClick}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
      title={
        <Space>
          <Text type="secondary">#{combo.id}</Text>
          <Tag color={getRewardColor(combo.reward_type)} icon={<GiftOutlined />}>
            +{combo.reward_amount} {combo.reward_type}
          </Tag>
        </Space>
      }
    >
      <Flex vertical gap="small" style={{ width: '100%' }}>
        <Text type="secondary">Conditions:</Text>
        <Space wrap>
          {conditions.map((condition, idx) => (
            <ConditionTag key={idx} condition={condition} />
          ))}
        </Space>
      </Flex>
    </Card>
  );
}

export default ComboCard;
