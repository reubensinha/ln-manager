export type searchSeriesResponse= {
    external_id: string;
    title: string;
    volumes?: number;
    chapters?: number;
    language?: string;
    orig_language?: string;
    img_url?: string;
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

type PluginRoute = {
    path: string;
    component: string;
}

type PluginNavBarLink = {
    label: string;
    icon?: string;
    link: string;
}

export type PluginResponse = {
    id: string;
    name: string;
    type: string;
    version: string;
    description?: string;
    routes?: PluginRoute[];
    navbarLinks?: PluginNavBarLink[];
}