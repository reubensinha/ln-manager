import type {
  ExternalLink,
  PublishingStatus,
  StaffRole,
} from "../types/MetadataFieldTypes";

export type SearchSeriesResponse = {
  external_id: string;
  title: string;
  volumes?: number;
  chapters?: number;
  language?: string;
  orig_language?: string;
  img_url?: string;
  nsfw_img: boolean;
};

export type SeriesGroupsResponse = {
  id: string;
  title: string;
  main_series_id: string;
  description?: string;
  img_url?: string;
  series?: Series[];
  nsfw_img?: boolean;
  monitored: boolean;
  download_status: string;
};

export type Release = {
  id: string;
  external_id?: string;
  title: string;
  romaji?: string;
  description?: string;
  url?: string;
  format?: string;
  language?: string;
  release_date?: string; // ISO 8601 date string (YYYY-MM-DD).
  isbn?: string;
  links?: ExternalLink[];
  source_url?: string;
  deleted?: boolean;
  book_id?: string;
  book?: Book;
  chapter_id?: string;
  chapter?: Chapter;
};

export type Chapter = {
  id: string;
  title: string;
  author?: string;
  number?: number;
  volume?: number;
  release_date?: string; // ISO 8601 date string (YYYY-MM-DD).
  description?: string;
  deleted?: boolean;
  series_id?: string;
  series?: Series;
  releases?: Release[];
};

export type Book = {
  id: string;
  external_id?: string;
  title: string;
  romaji?: string;
  title_orig?: string;
  description?: string;
  img_url?: string;
  language?: string;
  orig_language?: string;
  release_date?: string; // ISO 8601 date string (YYYY-MM-DD).
  authors?: string[];
  artists?: string[];
  other_staff?: StaffRole[];
  sort_order?: number;
  source_url?: string;
  nsfw_img: boolean;
  deleted: boolean;
  monitored: boolean;
  downloaded: boolean;

  series_id?: string;
  releases?: Release[];
};

export interface SeriesSourceResponse {
  external_id: string;
  title: string;
  romaji?: string;
  title_orig?: string;
  aliases?: string[];
  description?: string;
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
  source_url?: string;
  nsfw_img: boolean;
  deleted?: boolean;
  books?: Book[];
  chapters?: Chapter[];
}

export interface Series extends SeriesSourceResponse {
  id: string;
  plugin: PluginResponse;
  deleted: boolean;
  monitored: boolean;
  download_status: string;
}

type PluginRoute = {
  path: string;
  component: string;
};

type PluginNavBarLink = {
  label: string;
  icon?: string;
  link: string;
};

export type PluginResponse = {
  id: string;
  name: string;
  type: string;
  version: string;
  description?: string;
  routes?: PluginRoute[];
  navbarLinks?: PluginNavBarLink[];
};
