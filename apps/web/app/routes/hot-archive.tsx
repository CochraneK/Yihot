// 历史热榜归档：把每天结算的榜单快照按日期倒序陈列，可点进事件页。
// 纯读 hot_daily，不跑模型；与实时热榜 /hot 是两个页面。
import { SITE, withSubject } from "@aihot/industry/site";
import { Link, useLoaderData } from "react-router";
import type { HotArchiveDay, HotArchiveEntry, HotArchiveResponse } from "@aihot/contracts/site";
import { loadOr404 } from "../lib/api.server";
import { pageMeta } from "../lib/seo";
import { beijingWeekday } from "../lib/format";
import { Badge } from "../components/ui/Badge";
import { EmptyState } from "../components/ui/Page";
import { IconChevronDown } from "../components/icons";

export async function loader({ request }: { request: Request }) {
  const archive = await loadOr404<HotArchiveResponse>("/api/site/hot/archive", { signal: request.signal });
  return { archive };
}

export function meta() {
  return pageMeta({
    title: `${withSubject("热点")} · 历史榜单`,
    description: `${SITE.name}每日热点榜单归档，按日期回看每天都讨论过哪些公益事件。`,
    path: "/hot/archive",
    image: "/og/pages/hot.png",
  });
}

export function headers() {
  return { "Cache-Control": "public, max-age=0, s-maxage=600, stale-while-revalidate=300" };
}

const RANK_COLOR = ["text-rank-1", "text-rank-2", "text-rank-3"];
const rankColor = (rank: number) => RANK_COLOR[rank - 1] ?? "text-rank-rest";
const pad = (rank: number) => String(rank).padStart(2, "0");

const BADGES: Record<HotArchiveEntry["badges"][number], { label: string; tone: "hot" | "accent" | "amber" }> = {
  surge: { label: "爆", tone: "hot" },
  new: { label: "新", tone: "accent" },
  rising: { label: "发酵中", tone: "amber" },
};

/** YYYY-MM-DD -> 月/日 + 周几（北京时间日期，与榜单结算口径一致）。 */
function dayParts(day: string) {
  const [, mm, dd] = day.split("-");
  return { monthDay: `${Number(mm)}月${Number(dd)}日`, weekday: beijingWeekday(day).replace("星期", "周") };
}

function ArchiveRow({ e }: { e: HotArchiveEntry }) {
  const title = e.storyPublicId ? (
    <Link to={`/story/${e.storyPublicId}`} prefetch="intent" className="transition-colors hover:text-accent">{e.title}</Link>
  ) : e.title;
  return (
    <li className="flex items-start gap-3 px-4 py-2.5 sm:gap-4 sm:px-5">
      <span className={`mono w-6 shrink-0 text-[15px] font-semibold leading-6 ${rankColor(e.rank)}`}>{pad(e.rank)}</span>
      <div className="min-w-0 flex-1">
        <p className="text-[14px] font-[600] leading-[1.55] text-ink">{title}</p>
        <p className="mt-0.5 text-[12px] text-ink-4">
          <span className="num">{e.sourceCount}</span> 个来源 · <span className="num">{e.participantCount}</span> 位参与者
          {e.badges.length > 0 && (
            <span className="ml-2 inline-flex gap-1 align-middle">
              {e.badges.map((b) => <Badge key={b} tone={BADGES[b].tone}>{BADGES[b].label}</Badge>)}
            </span>
          )}
        </p>
      </div>
      <span className="mono hidden shrink-0 text-[16px] font-semibold leading-6 text-ink sm:block">{Math.round(e.heat)}</span>
    </li>
  );
}

function DayCard({ d, open }: { d: HotArchiveDay; open: boolean }) {
  const parts = dayParts(d.day);
  return (
    <details className="card group/day overflow-hidden" open={open}>
      <summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-3.5 sm:px-5 [&::-webkit-details-marker]:hidden">
        <span className="flex w-12 shrink-0 flex-col items-center">
          <span className="num text-[20px] font-black leading-none tracking-[-0.03em] text-ink">{d.day.slice(8, 10)}</span>
          <span className="mt-1 text-[10px] leading-none text-ink-4">{parts.weekday}</span>
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-[14px] font-bold text-ink">{parts.monthDay} 热点榜</span>
          <span className="mt-0.5 block text-[12px] text-ink-4">
            {d.entries.length > 0 ? <><span className="num">{d.entries.length}</span> 件事</> : "当日无入选事件"}
          </span>
        </span>
        <IconChevronDown size={16} className="shrink-0 text-ink-4 transition-transform duration-200 group-open/day:rotate-180" />
      </summary>
      {d.entries.length > 0 && (
        <ol className="divide-y divide-line-soft border-t border-line-soft">
          {d.entries.map((e) => <ArchiveRow key={`${e.rank}-${e.storyPublicId ?? e.title}`} e={e} />)}
        </ol>
      )}
    </details>
  );
}

export default function HotArchivePage() {
  const { archive } = useLoaderData<typeof loader>();
  const days = archive.days;
  const totalEvents = days.reduce((n, d) => n + d.entries.length, 0);
  return (
    <div className="pb-10">
      <header className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2 pb-5 pt-5 lg:pt-1">
        <div>
          <div className="flex items-center gap-2 text-[12px] font-semibold tracking-[0.08em] text-hot">
            <span className="relative flex size-2" aria-hidden="true">
              <span className="relative inline-flex size-2 rounded-full bg-hot" />
            </span>
            历史榜单
          </div>
          <h1 className="mt-1.5 text-[24px] font-bold leading-[1.3] tracking-[-0.01em] text-ink lg:text-[26px]">{withSubject("热点")} · 归档</h1>
          <p className="mt-1.5 text-[13.5px] text-ink-3">
            按北京时间逐日结算的榜单快照，共 <span className="num">{days.length}</span> 天、<span className="num">{totalEvents}</span> 条入选事件
          </p>
        </div>
        <Link to="/hot" className="text-[13px] text-accent hover:underline">看当前热榜 →</Link>
      </header>

      {days.length === 0 || totalEvents === 0 ? (
        <div className="card rounded-sheet">
          <EmptyState title="还没有归档榜单">每天的榜单结算后会出现在这里。</EmptyState>
        </div>
      ) : (
        <div className="grid gap-3">
          {days.map((d, i) => <DayCard key={d.day} d={d} open={i === 0} />)}
        </div>
      )}
    </div>
  );
}
