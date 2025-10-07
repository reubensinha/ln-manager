import type { ExternalLink, PublishingStatus, StaffRole } from "../types/MetadataFieldTypes";

export type SearchSeriesResponse= {
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


export type Book = {
  id: string;
  title: string;
  img_url: string;
  link?: string;
  in_library?: boolean;
  description?: string;
};


export interface SeriesSourceResponse {
    external_id: string;
    title: string;
    romaji?: string;
    title_orig?: string;
    aliases?: string[];
    description?: string;
    volumes?: number;
    chapters?: number;
    language?: string;
    orig_language?: string;
    img_url?: string;
    publishing_status?: PublishingStatus;
    external_links?: ExternalLink[];
    start_date?: string; // ISO 8601 date string (YYYY-MM-DD).
    end_date?: string; // ISO 8601 date string (YYYY-MM-DD).
    publishers?: string[];
    authors?: string[];
    artists?: string[];
    other_staff?: StaffRole[];
    genres?: string[];
    tags?: string[];
    demographics?: string[];
    content_tags?: string[];
    books?: Book[];
}

export interface Series extends SeriesSourceResponse {
    id: string;
}


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