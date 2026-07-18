import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AXIS_TEXT, GRID, heatColor, SERIES, TOOLTIP_STYLE } from "../chartTheme";

interface ChartData {
  kind: string;
  data: Record<string, any>[];
  x: string;
  y: string[];
  title: string;
  meta?: { labels?: string[] };
}

const axisProps = {
  stroke: GRID,
  tick: { fill: AXIS_TEXT, fontSize: 11, fontFamily: '"IBM Plex Mono", monospace' },
  tickLine: false,
} as const;

function Heatmap({ chart }: { chart: ChartData }) {
  const labels = chart.meta?.labels ?? [];
  const max = Math.max(...chart.data.map((d) => d.value as number), 1);
  const n = labels.length || Math.sqrt(chart.data.length);
  const cell = (row: string, col: string) =>
    chart.data.find((d) => d.y === row && d.x === col)?.value ?? 0;

  return (
    <div className="p-2">
      <div className="text-xs mb-2" style={{ color: AXIS_TEXT }}>
        {chart.title} — rows: actual, columns: predicted
      </div>
      <div
        className="grid gap-[2px] font-mono text-xs"
        style={{ gridTemplateColumns: `auto repeat(${n}, minmax(2rem, 3rem))` }}
      >
        <div />
        {labels.map((l) => (
          <div key={`c${l}`} className="text-center pb-1" style={{ color: AXIS_TEXT }}>
            {l}
          </div>
        ))}
        {labels.map((row) => (
          <>
            <div key={`r${row}`} className="pr-2 text-right self-center" style={{ color: AXIS_TEXT }}>
              {row}
            </div>
            {labels.map((col) => {
              const v = cell(row, col);
              return (
                <div
                  key={`${row}-${col}`}
                  title={`actual ${row}, predicted ${col}: ${v}`}
                  className="aspect-square rounded flex items-center justify-center"
                  style={{
                    background: heatColor(v, max),
                    color: v / max > 0.55 ? "#0b0e14" : "#e8edf5",
                  }}
                >
                  {v}
                </div>
              );
            })}
          </>
        ))}
      </div>
    </div>
  );
}

export default function ChartPreview({ chart }: { chart: ChartData }) {
  if (chart.kind === "heatmap") return <Heatmap chart={chart} />;

  const common = (
    <>
      <CartesianGrid stroke={GRID} strokeDasharray="0" vertical={false} />
      <XAxis dataKey={chart.x} {...axisProps} name={chart.x} />
      <YAxis {...axisProps} width={46} />
      <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ stroke: GRID }} />
      {chart.y.length > 1 && <Legend wrapperStyle={{ fontSize: 12, color: AXIS_TEXT }} />}
    </>
  );

  return (
    <div className="h-64 w-full">
      {chart.title && (
        <div className="text-xs px-2 pt-1" style={{ color: AXIS_TEXT }}>
          {chart.title}
        </div>
      )}
      <ResponsiveContainer width="100%" height="100%">
        {chart.kind === "bar" ? (
          <BarChart data={chart.data} barCategoryGap="20%">
            {common}
            {chart.y.map((col, i) => (
              <Bar key={col} dataKey={col} fill={SERIES[i % SERIES.length]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        ) : chart.kind === "scatter" ? (
          <ScatterChart>
            {common}
            {chart.y.map((col, i) => (
              <Scatter
                key={col}
                name={col}
                data={chart.data}
                dataKey={col}
                fill={SERIES[i % SERIES.length]}
                stroke="#121722"
                strokeWidth={2}
              />
            ))}
          </ScatterChart>
        ) : (
          <LineChart data={chart.data}>
            {common}
            {chart.y.map((col, i) => (
              <Line
                key={col}
                type="monotone"
                dataKey={col}
                stroke={SERIES[i % SERIES.length]}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
