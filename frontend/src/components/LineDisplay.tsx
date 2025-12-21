/**
 * LineDisplay - Display a line of players with stats and bonuses
 */

import { Card, Row, Col, Tag, Space, Typography, Divider, Statistic } from 'antd';
import { TrophyOutlined, TeamOutlined } from '@ant-design/icons';
import type { Player, PlayerInfo, ConcreteLineResponse, LineSolution } from '../api/types';
import { PlayerCard } from './PlayerCard';

const { Text } = Typography;

interface LineDisplayProps {
  // Either a LineSolution (from optimization) or ConcreteLineResponse (from Goal 1)
  line: LineSolution | ConcreteLineResponse;
  rank?: number;
  showDetails?: boolean;
}

// Type guard to check if it's a LineSolution
function isLineSolution(line: LineSolution | ConcreteLineResponse): line is LineSolution {
  return 'total_base_ovr' in line;
}

export function LineDisplay({ line, rank, showDetails = true }: LineDisplayProps) {
  const players = line.players;
  const isOptimization = isLineSolution(line);

  return (
    <Card
      title={
        <Space>
          <TeamOutlined />
          {rank !== undefined && <Tag color="blue">#{rank}</Tag>}
          <Text strong>
            {players.map((p) => `${p.first_name.charAt(0)}. ${p.last_name}`).join(' - ')}
          </Text>
        </Space>
      }
      extra={
        <Space>
          {isOptimization ? (
            <Tag color="green" style={{ fontSize: 14, padding: '4px 8px' }}>
              {line.effective_ovr} Effective OVR
            </Tag>
          ) : (
            <Tag color="green" style={{ fontSize: 14, padding: '4px 8px' }}>
              {line.ranking_score.toFixed(1)} Score
            </Tag>
          )}
        </Space>
      }
    >
      {/* Players */}
      <Row gutter={[8, 8]}>
        {players.map((player, idx) => (
          <Col key={idx} xs={24} sm={12} md={8} lg={players.length <= 2 ? 12 : 8}>
            <PlayerCard player={player as Player | PlayerInfo} compact />
          </Col>
        ))}
      </Row>

      {showDetails && (
        <>
          <Divider />
          
          {/* Stats */}
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="Total OVR"
                value={isOptimization ? line.total_base_ovr : line.total_ovr}
              />
            </Col>
            {isOptimization && (
              <Col span={6}>
                <Statistic
                  title="OVR Bonus"
                  value={line.ovr_bonus}
                  prefix="+"
                />
              </Col>
            )}
            <Col span={6}>
              <Statistic
                title="Salary"
                value={isOptimization ? line.total_salary : line.total_salary}
                suffix="K"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="AP Cost"
                value={isOptimization ? line.total_ap : line.total_ap}
              />
            </Col>
          </Row>

          {/* Active Combos */}
          {isOptimization && line.active_combos && line.active_combos.length > 0 && (
            <>
              <Divider>
                <Space>
                  <TrophyOutlined />
                  Active Combos
                </Space>
              </Divider>
              <Space wrap>
                {line.active_combos.map((combo, idx) => (
                  <Tag key={idx} color="gold">
                    +{combo.reward_amount} {combo.reward_type}: {combo.description}
                  </Tag>
                ))}
              </Space>
            </>
          )}

          {/* For ConcreteLineResponse, show combo IDs */}
          {!isOptimization && line.activated_combo_ids && line.activated_combo_ids.length > 0 && (
            <>
              <Divider>
                <Space>
                  <TrophyOutlined />
                  Active Combo IDs
                </Space>
              </Divider>
              <Space wrap>
                {line.activated_combo_ids.map((id) => (
                  <Tag key={id} color="gold">Combo #{id}</Tag>
                ))}
              </Space>
            </>
          )}
        </>
      )}
    </Card>
  );
}

export default LineDisplay;
