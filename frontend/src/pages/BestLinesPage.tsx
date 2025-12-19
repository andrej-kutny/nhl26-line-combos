/**
 * BestLinesPage - Display Goal 1 results (best line combinations)
 */

import { useState } from 'react';
import {
  Card,
  Tabs,
  Select,
  Flex,
  Typography,
  Row,
  Col,
  Alert,
  Empty,
  Spin,
  Statistic,
  Pagination,
} from 'antd';
import { TrophyOutlined } from '@ant-design/icons';
import { useApi } from '../hooks/useApi';
import { getBestLines, listRuns } from '../api/best';
import { LineDisplay } from '../components/LineDisplay';

const { Title, Text } = Typography;

type PositionType = 'forward' | 'defense';
type OptimizationMode = 'ovr' | 'sal' | 'ap' | 'ovr_sal' | 'ovr_sal_ap';

const OPTIMIZATION_MODES: { value: OptimizationMode; label: string }[] = [
  { value: 'ovr', label: 'Best OVR' },
  { value: 'sal', label: 'Best Salary' },
  { value: 'ap', label: 'Best AP' },
  { value: 'ovr_sal', label: 'OVR + Salary' },
  { value: 'ovr_sal_ap', label: 'OVR + Salary + AP' },
];

export function BestLinesPage() {
  const [positionType, setPositionType] = useState<PositionType>('forward');
  const [mode, setMode] = useState<OptimizationMode>('ovr');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Fetch runs list (for future use in run selector)
  const { loading: loadingRuns } = useApi(
    () => listRuns(positionType),
    [positionType]
  );

  // Fetch best lines
  const { data: linesData, loading: loadingLines, error } = useApi(
    () => getBestLines(positionType, mode, {
      limit: pageSize,
      offset: (page - 1) * pageSize,
    }),
    [positionType, mode, page]
  );

  const handlePositionChange = (key: string) => {
    setPositionType(key as PositionType);
    setPage(1);
  };

  const handleModeChange = (value: OptimizationMode) => {
    setMode(value);
    setPage(1);
  };

  return (
    <Flex vertical gap="large" style={{ width: '100%' }}>
      <Title level={2}>
        <TrophyOutlined /> Best Lines (Goal 1 Results)
      </Title>

      <Text type="secondary">
        Pre-computed optimal line combinations ranked by different optimization criteria.
      </Text>

      {/* Position Tabs */}
      <Card>
        <Tabs
          activeKey={positionType}
          onChange={handlePositionChange}
          items={[
            {
              key: 'forward',
              label: 'Forward Lines',
            },
            {
              key: 'defense',
              label: 'Defense Pairs',
            },
          ]}
        />

        {/* Mode Selector */}
        <Row gutter={16} align="middle" style={{ marginTop: 16 }}>
          <Col>
            <Text strong>Optimization Mode:</Text>
          </Col>
          <Col>
            <Select
              value={mode}
              onChange={handleModeChange}
              options={OPTIMIZATION_MODES}
              style={{ width: 200 }}
            />
          </Col>
        </Row>
      </Card>

      {/* Run Info */}
      {linesData?.run && (
        <Card size="small">
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="Run ID"
                value={linesData.run.id}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Total Lines"
                value={linesData.total_lines}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Run Timestamp"
                value={new Date(linesData.run.run_timestamp).toLocaleString()}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Error */}
      {error && (
        <Alert
          title="Failed to load best lines"
          description={error}
          type="error"
          showIcon
        />
      )}

      {/* Loading */}
      {(loadingLines || loadingRuns) && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
        </div>
      )}

      {/* No Data */}
      {!loadingLines && !error && (!linesData?.lines || linesData.lines.length === 0) && (
        <Empty
          description={
            <span>
              No best lines found for {positionType} / {mode}.
              <br />
              Run the Goal 1 pipeline to generate results.
            </span>
          }
        />
      )}

      {/* Lines List */}
      {!loadingLines && linesData?.lines && linesData.lines.length > 0 && (
        <Flex vertical gap="middle" style={{ width: '100%' }}>
          {linesData.lines.map((line, idx) => (
            <LineDisplay
              key={line.id}
              line={line}
              rank={(page - 1) * pageSize + idx + 1}
            />
          ))}

          {/* Pagination */}
          <Row justify="center" style={{ marginTop: 16 }}>
            <Pagination
              current={page}
              pageSize={pageSize}
              total={linesData.total_lines}
              onChange={setPage}
              showSizeChanger={false}
              showTotal={(total) => `${total} lines total`}
            />
          </Row>
        </Flex>
      )}
    </Flex>
  );
}

export default BestLinesPage;
