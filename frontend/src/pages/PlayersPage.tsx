/**
 * PlayersPage - Browse and search players
 */

import { useState, useMemo } from 'react';
import {
  Card,
  Table,
  Tabs,
  Input,
  Select,
  Row,
  Col,
  Tag,
  Space,
  Flex,
  Typography,
  Alert,
  Slider,
} from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useApi } from '../hooks/useApi';
import { getForwards, getDefense, getGoalies, getTeams, getEvents } from '../api/players';
import type { Player } from '../api/types';

const { Title } = Typography;

// Get color based on overall rating
function getOvrColor(ovr: number): string {
  if (ovr >= 90) return 'green';
  if (ovr >= 85) return 'blue';
  if (ovr >= 80) return 'purple';
  if (ovr >= 75) return 'gold';
  return 'default';
}

// Table columns definition
const columns: ColumnsType<Player> = [
  {
    title: 'Name',
    key: 'name',
    render: (_, player) => `${player.first_name} ${player.last_name}`,
    sorter: (a, b) => a.last_name.localeCompare(b.last_name),
  },
  {
    title: 'OVR',
    dataIndex: 'overall',
    key: 'overall',
    sorter: (a, b) => a.overall - b.overall,
    defaultSortOrder: 'descend',
    render: (ovr) => <Tag color={getOvrColor(ovr)}>{ovr}</Tag>,
    width: 80,
  },
  {
    title: 'Team',
    dataIndex: 'team',
    key: 'team',
    width: 80,
  },
  {
    title: 'Nationality',
    dataIndex: 'nationality',
    key: 'nationality',
    width: 100,
  },
  {
    title: 'Event',
    dataIndex: 'event',
    key: 'event',
    render: (event) => event ? <Tag color="purple">{event}</Tag> : '-',
    width: 120,
  },
  {
    title: 'Salary',
    dataIndex: 'salary',
    key: 'salary',
    sorter: (a, b) => a.salary - b.salary,
    render: (salary) => `${salary}K`,
    width: 80,
  },
];

interface FiltersState {
  search: string;
  team?: string;
  event?: string;
  ovrRange: [number, number];
}

export function PlayersPage() {
  const [activeTab, setActiveTab] = useState<'FWD' | 'DEF' | 'G'>('FWD');
  const [filters, setFilters] = useState<FiltersState>({
    search: '',
    ovrRange: [60, 99],
  });

  // Fetch data
  const { data: forwards, loading: loadingFwd, error: errorFwd } = useApi(() => getForwards(), []);
  const { data: defense, loading: loadingDef, error: errorDef } = useApi(() => getDefense(), []);
  const { data: goalies, loading: loadingG, error: errorG } = useApi(() => getGoalies(), []);
  const { data: teams } = useApi(() => getTeams(), []);
  const { data: events } = useApi(() => getEvents(), []);

  // Get current players based on tab
  const currentPlayers = useMemo(() => {
    switch (activeTab) {
      case 'FWD': return forwards || [];
      case 'DEF': return defense || [];
      case 'G': return goalies || [];
    }
  }, [activeTab, forwards, defense, goalies]);

  const isLoading = activeTab === 'FWD' ? loadingFwd : activeTab === 'DEF' ? loadingDef : loadingG;
  const error = activeTab === 'FWD' ? errorFwd : activeTab === 'DEF' ? errorDef : errorG;

  // Filter players
  const filteredPlayers = useMemo(() => {
    return currentPlayers.filter((player) => {
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const fullName = `${player.first_name} ${player.last_name}`.toLowerCase();
        if (!fullName.includes(searchLower)) {
          return false;
        }
      }
      // Team filter
      if (filters.team && player.team !== filters.team) {
        return false;
      }
      // Event filter
      if (filters.event && player.event !== filters.event) {
        return false;
      }
      // OVR range filter
      if (player.overall < filters.ovrRange[0] || player.overall > filters.ovrRange[1]) {
        return false;
      }
      return true;
    });
  }, [currentPlayers, filters]);

  return (
    <Flex vertical gap="large" style={{ width: '100%' }}>
      <Title level={2}>Players</Title>

      {error && (
        <Alert title="Failed to load players" description={error} type="error" showIcon />
      )}

      {/* Filters */}
      <Card size="small">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Input
              prefix={<SearchOutlined />}
              placeholder="Search by name..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="Team"
              value={filters.team}
              onChange={(value) => setFilters({ ...filters, team: value })}
              options={teams?.map((t) => ({ label: t, value: t })) || []}
              allowClear
              style={{ width: '100%' }}
              showSearch
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="Event"
              value={filters.event}
              onChange={(value) => setFilters({ ...filters, event: value })}
              options={events?.map((e) => ({ label: e, value: e })) || []}
              allowClear
              style={{ width: '100%' }}
              showSearch
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space style={{ width: '100%' }}>
              <span>OVR:</span>
              <Slider
                range
                min={60}
                max={99}
                value={filters.ovrRange}
                onChange={(value) => setFilters({ ...filters, ovrRange: value as [number, number] })}
                style={{ flex: 1, minWidth: 120 }}
              />
              <span>{filters.ovrRange[0]}-{filters.ovrRange[1]}</span>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Players Table with Tabs */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as 'FWD' | 'DEF' | 'G')}
          items={[
            { key: 'FWD', label: `Forwards (${forwards?.length || 0})` },
            { key: 'DEF', label: `Defense (${defense?.length || 0})` },
            { key: 'G', label: `Goalies (${goalies?.length || 0})` },
          ]}
        />
        <Table
          columns={columns}
          dataSource={filteredPlayers}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `${total} players`,
          }}
          size="small"
          scroll={{ x: 800 }}
        />
      </Card>
    </Flex>
  );
}

export default PlayersPage;
