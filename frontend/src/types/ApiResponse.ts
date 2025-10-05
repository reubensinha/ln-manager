export type searchSeriesResponse= {
    external_id: string;
    title: string;
    volumes: number | null;
    chapters: number | null;
    language: string | null;
    orig_language: string | null;
    img_url: string | null;
}

export type SeriesGroupsResponse = {
    id: string;
    title: string;
    img_url: string;
    series: {
        id: string;
        source: string;
    }[];
};