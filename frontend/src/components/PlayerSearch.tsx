/**
 * PlayerSearch - Autocomplete player lookup component
 */

import { useState, useCallback } from 'react';
import { AutoComplete, Input, Space, Tag, Typography } from 'antd';
import { SearchOutlined, UserOutlined } from '@ant-design/icons';
import { lookupPlayers } from '../api/players';
import type { LookupOption } from '../api/types';
import { useLazyApi } from '../hooks/useApi';

const { Text } = Typography;

interface PlayerSearchProps {
  mode?: 'card' | 'player';
  position?: 'FWD' | 'DEF' | 'G';
  placeholder?: string;
  onSelect?: (option: LookupOption) => void;
  style?: React.CSSProperties;
}

export function PlayerSearch({
  mode = 'card',
  position,
  placeholder = 'Search players...',
  onSelect,
  style,
}: PlayerSearchProps) {
  const [searchValue, setSearchValue] = useState('');
  const { data: options, loading, execute } = useLazyApi(
    (q: string) => lookupPlayers(q, mode, position)
  );

  const handleSearch = useCallback(
    async (value: string) => {
      setSearchValue(value);
      if (value.length >= 2) {
        await execute(value);
      }
    },
    [execute]
  );

  const handleSelect = useCallback(
    (_value: string, option: { data: LookupOption }) => {
      if (onSelect) {
        onSelect(option.data);
      }
      setSearchValue('');
    },
    [onSelect]
  );

  const renderOption = (option: LookupOption) => ({
    value: String(option.value),
    label: (
      <Space>
        <UserOutlined />
        <Text strong>{option.label}</Text>
        <Tag color="blue">{option.position}</Tag>
        <Tag color="green">{option.overall} OVR</Tag>
        {option.event && <Tag color="purple">{option.event}</Tag>}
      </Space>
    ),
    data: option,
  });

  return (
    <AutoComplete
      style={{ width: '100%', ...style }}
      options={options?.map(renderOption) || []}
      onSearch={handleSearch}
      onSelect={handleSelect}
      value={searchValue}
      notFoundContent={loading ? 'Searching...' : searchValue.length >= 2 ? 'No players found' : null}
    >
      <Input
        prefix={<SearchOutlined />}
        placeholder={placeholder}
        allowClear
      />
    </AutoComplete>
  );
}

export default PlayerSearch;
