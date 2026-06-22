/** Central registry of React Query cache keys for the series slice. */
export const queryKeys = {
  seriesGroups: ["seriesGroups"] as const,
  seriesGroup: (id: string) => ["seriesGroups", id] as const,
  seriesList: ["series"] as const,
  series: (id: string) => ["series", id] as const,
  releases: ["releases"] as const,
  metadataSources: ["metadataSources"] as const,
  seriesFromSource: (sourceId: string, externalId: string) =>
    ["seriesFromSource", sourceId, externalId] as const,
  search: (source: string, query: string) => ["search", source, query] as const,
};
