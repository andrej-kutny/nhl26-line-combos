/**
 * OptimizePage - Line optimization form
 */

import { useState } from 'react';
import {
  Card,
  Form,
  Select,
  InputNumber,
  Button,
  Space,
  Flex,
  Typography,
  Row,
  Col,
  Divider,
  Alert,
  Spin,
  Empty,
} from 'antd';
import { RocketOutlined, ReloadOutlined } from '@ant-design/icons';
import { useApi, useLazyApi } from '../hooks/useApi';
import { getTeams, getNationalities, getEvents } from '../api/players';
import { optimizeForwardLine, optimizeDefensePair } from '../api/optimize';
import { LineDisplay } from '../components/LineDisplay';
import type { OptimizationRequest, OptimizationResponse } from '../api/types';

const { Title, Paragraph } = Typography;

type PositionType = 'forward' | 'defense';
type OptimizationTarget = 'ovr' | 'salary' | 'ap' | 'balanced';

interface FormValues {
  position_type: PositionType;
  optimization_target: OptimizationTarget;
  min_ovr?: number;
  max_salary?: number;
  max_ap?: number;
  required_team?: string;
  required_nationality?: string;
  required_event?: string;
  num_solutions: number;
}

export function OptimizePage() {
  const [form] = Form.useForm<FormValues>();
  const [results, setResults] = useState<OptimizationResponse | null>(null);

  // Fetch filter options
  const { data: teams } = useApi(() => getTeams(), []);
  const { data: nationalities } = useApi(() => getNationalities(), []);
  const { data: events } = useApi(() => getEvents(), []);

  // Optimization mutation
  const { loading: optimizing, error, execute: runOptimization } = useLazyApi(
    async (values: FormValues) => {
      const request: OptimizationRequest = {
        constraints: {
          min_ovr: values.min_ovr,
          max_salary: values.max_salary,
          max_ap: values.max_ap,
          required_team: values.required_team,
          required_nationality: values.required_nationality,
          required_event: values.required_event,
        },
        optimization_target: values.optimization_target,
        num_solutions: values.num_solutions,
      };

      if (values.position_type === 'forward') {
        return optimizeForwardLine(request);
      } else {
        return optimizeDefensePair(request);
      }
    }
  );

  const handleSubmit = async (values: FormValues) => {
    const result = await runOptimization(values);
    if (result) {
      setResults(result);
    }
  };

  const handleReset = () => {
    form.resetFields();
    setResults(null);
  };

  return (
    <Flex vertical gap="large" style={{ width: '100%' }}>
      <Title level={2}>Optimize Lines</Title>

      <Row gutter={24}>
        {/* Form */}
        <Col xs={24} lg={8}>
          <Card title="Optimization Settings">
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              initialValues={{
                position_type: 'forward',
                optimization_target: 'ovr',
                num_solutions: 5,
              }}
            >
              <Form.Item
                name="position_type"
                label="Position Type"
                rules={[{ required: true }]}
              >
                <Select
                  options={[
                    { label: 'Forward Line (3 players)', value: 'forward' },
                    { label: 'Defense Pair (2 players)', value: 'defense' },
                  ]}
                />
              </Form.Item>

              <Form.Item
                name="optimization_target"
                label="Optimization Target"
                rules={[{ required: true }]}
              >
                <Select
                  options={[
                    { label: 'Maximum OVR', value: 'ovr' },
                    { label: 'Minimum Salary', value: 'salary' },
                    { label: 'Minimum AP Cost', value: 'ap' },
                    { label: 'Balanced', value: 'balanced' },
                  ]}
                />
              </Form.Item>

              <Divider>Constraints (Optional)</Divider>

              <Form.Item name="min_ovr" label="Minimum OVR">
                <InputNumber min={60} max={99} style={{ width: '100%' }} placeholder="e.g., 85" />
              </Form.Item>

              <Form.Item name="max_salary" label="Maximum Salary (K)">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="e.g., 300" />
              </Form.Item>

              <Form.Item name="max_ap" label="Maximum AP Cost">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="e.g., 10" />
              </Form.Item>

              <Form.Item name="required_team" label="Required Team">
                <Select
                  options={teams?.map((t) => ({ label: t, value: t })) || []}
                  allowClear
                  showSearch
                  placeholder="Any team"
                />
              </Form.Item>

              <Form.Item name="required_nationality" label="Required Nationality">
                <Select
                  options={nationalities?.map((n) => ({ label: n, value: n })) || []}
                  allowClear
                  showSearch
                  placeholder="Any nationality"
                />
              </Form.Item>

              <Form.Item name="required_event" label="Required Event">
                <Select
                  options={events?.map((e) => ({ label: e, value: e })) || []}
                  allowClear
                  showSearch
                  placeholder="Any event"
                />
              </Form.Item>

              <Divider>Results</Divider>

              <Form.Item
                name="num_solutions"
                label="Number of Solutions"
                rules={[{ required: true }]}
              >
                <InputNumber min={1} max={20} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item>
                <Space style={{ width: '100%' }}>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<RocketOutlined />}
                    loading={optimizing}
                    block
                  >
                    Optimize
                  </Button>
                  <Button icon={<ReloadOutlined />} onClick={handleReset}>
                    Reset
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* Results */}
        <Col xs={24} lg={16}>
          <Card title="Results">
            {error && (
              <Alert title="Optimization Failed" description={error} type="error" showIcon />
            )}

            {optimizing && (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Spin size="large" />
                <Paragraph style={{ marginTop: 16 }}>Running optimization...</Paragraph>
              </div>
            )}

            {!optimizing && !results && !error && (
              <Empty description="Configure settings and click Optimize to find the best lines" />
            )}

            {results && (
              <Flex vertical gap="middle" style={{ width: '100%' }}>
                {results.success ? (
                  <>
                    <Alert
                      title={`Found ${results.solutions.length} solutions`}
                      description={`Evaluated ${results.candidates_evaluated} candidates in ${results.computation_time_ms}ms`}
                      type="success"
                      showIcon
                    />
                    {results.solutions.map((solution, idx) => (
                      <LineDisplay key={idx} line={solution} rank={solution.rank} />
                    ))}
                  </>
                ) : (
                  <Alert
                    title="No solutions found"
                    description={results.message}
                    type="warning"
                    showIcon
                  />
                )}
              </Flex>
            )}
          </Card>
        </Col>
      </Row>
    </Flex>
  );
}

export default OptimizePage;
