import type { Series, SeriesGroupsResponse } from "../api/ApiResponse";

/**
 * Places in the core UI where plugins may contribute a component.
 *
 * IDs are versioned: if a point's context shape changes incompatibly, publish a new
 * `/v2` id rather than editing this one, so existing plugins keep working.
 */
export const extensionPoints = {
  /** Series page, between the series details and the Books/Chapters tabs. */
  seriesDetailInline: "core/series/detail/inline/v1",
  /** Series page, below everything else. Scoped to the whole series group. */
  seriesDetailBottom: "core/series/detail/bottom/v1",
} as const;

/** Context handed to both series extension points. */
export interface SeriesSectionContext {
  /** The series for the metadata source tab currently in view. */
  series: Series;
  /** The group the series belongs to, including its other source editions. */
  seriesGroup: SeriesGroupsResponse;
}
