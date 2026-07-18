import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MetricPoint } from "../types";
import { AXIS_TEXT, GRID, LOSS_LINE, TOOLTIP_STYLE } from "./chartTheme";

/** Live single-series training curve, streamed from node_progress events. */
export default function LiveMetrics({ points }: { points: MetricPoint[] }) {
  if (!points.length) return null;
  const xKey = "epoch" in points[0] ? "epoch" : "step";
  const yKey = "loss" in points[0] ? "loss" : Object.keys(points[0]).find((k) => k !== xKey);
  if (!yKey) return null;

  return (
    <div>
      <div className="text-xs mb-1" style={{ color: AXIS_TEXT }}>
        {yKey} per {xKey} · live
      </div>
      <div className="h-36 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis
              dataKey={xKey}
              stroke={GRID}
              tick={{ fill: AXIS_TEXT, fontSize: 10, fontFamily: '"IBM Plex Mono", monospace' }}
              tickLine={false}
            />
            <YAxis
              stroke={GRID}
              tick={{ fill: AXIS_TEXT, fontSize: 10, fontFamily: '"IBM Plex Mono", monospace' }}
              tickLine={false}
              width={52}
              domain={["auto", "auto"]}
            />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ stroke: GRID }} />
            <Line
              type="monotone"
              dataKey={yKey}
              stroke={LOSS_LINE}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
