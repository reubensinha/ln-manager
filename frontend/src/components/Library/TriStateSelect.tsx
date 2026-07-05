import { Button, Group, Select, Stack, Text } from "@mantine/core";

export type TriState = "include" | "exclude";
/** Map of option value -> filter state. Absent keys mean "not filtered". */
export type TriStateValue = Record<string, TriState>;

interface TriStateSelectProps {
  label: string;
  placeholder?: string;
  options: { value: string; label: string }[];
  value: TriStateValue;
  onChange: (value: TriStateValue) => void;
  width?: number;
}

/**
 * A searchable dropdown to add filter values (handles long option lists), plus a chip
 * per active selection. Clicking a chip cycles include (teal) -> exclude ("≠", red) ->
 * removed. Adding from the dropdown starts a value at "include".
 */
export function TriStateSelect({
  label,
  placeholder = "Add…",
  options,
  value,
  onChange,
  width = 160,
}: TriStateSelectProps) {
  const available = options.filter((o) => !(o.value in value));

  const add = (v: string | null) => {
    if (v && !(v in value)) onChange({ ...value, [v]: "include" });
  };

  const cycle = (v: string) => {
    const next = { ...value };
    if (value[v] === "include") next[v] = "exclude";
    else delete next[v]; // exclude -> removed
    onChange(next);
  };

  const labelFor = (v: string) =>
    options.find((o) => o.value === v)?.label ?? v;

  return (
    <Stack gap={4}>
      <Text size="sm" fw={500}>
        {label}
      </Text>
      <Group gap={6} align="center">
        <Select
          placeholder={placeholder}
          data={available}
          value={null}
          onChange={add}
          searchable
          w={width}
          disabled={available.length === 0}
          comboboxProps={{ withinPortal: true }}
        />
        {Object.keys(value).map((v) => {
          const state = value[v];
          return (
            <Button
              key={v}
              size="xs"
              radius="xl"
              variant="filled"
              color={state === "exclude" ? "red" : "teal"}
              onClick={() => cycle(v)}
              title={
                state === "include"
                  ? `Only with ${labelFor(v)} — click to exclude`
                  : `Excluding ${labelFor(v)} — click to remove`
              }
            >
              {state === "exclude" ? `≠ ${labelFor(v)}` : labelFor(v)}
            </Button>
          );
        })}
      </Group>
    </Stack>
  );
}
