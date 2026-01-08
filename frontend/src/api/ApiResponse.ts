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
  metadata_source?: MetadataSource;
  group?: SeriesGroupsResponse;
  deleted: boolean;
  monitored: boolean;
  download_status: string;
  group_id?: string;
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
  author: string;
  description?: string;
  enabled: boolean;
  routes?: PluginRoute[];
  navbarLinks?: PluginNavBarLink[];
};

export type MetadataSource = {
  id: string;
  name: string;
  version: string;
  author?: string;
  description?: string;
  config?: Record<string, unknown>;
  enabled: boolean;
  plugin_id?: string;
  plugin?: PluginResponse;
};

export type PluginCapability = {
  id: string;
  name: string;
  description?: string;
  config_schema?: Record<string, unknown>;
};


export type Notification = {
  id: string;
  message: string;
  type: "INFO" | "WARNING" | "ERROR" | "SUCCESS";
  timestamp: string; // ISO 8601 date string
  read: boolean;
}

export type BackupInfo = {
  filename: string;
  path: string;
  size: number;
  created: string;
  version?: string;
  timestamp?: string;
}

export type TaskProgress = {
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  message: string;
  created_at: string;
  completed_at: string | null;
  result: unknown;
  error: string | null;
}

export type BackupResponse = {
  success: boolean;
  message: string;
  filename?: string;
  path?: string;
  size?: number;
}

export type BackupListResponse = {
  success: boolean;
  backups: BackupInfo[];
  count: number;
}

export type TaskResponse = {
  success: boolean;
  task_id: string;
  message: string;
}

export type TaskStatusResponse = {
  success: boolean;
  task: TaskProgress;
}

export type RestoreResponse = {
  success: boolean;
  message: string;
  summary?: {
    restored_tables: Record<string, number>;
    restored_files: number;
    backup_version: string | null;
    backup_timestamp: string | null;
  };
}

export type Indexer = {
  id: string;
  name: string;
  version: string;
  author?: string;
  description?: string;
  config?: Record<string, unknown>;
  enabled: boolean;
  plugin_id?: string;
  plugin?: PluginResponse;
}

export type DownloadClient = {
  id: string;
  name: string;
  version: string;
  author?: string;
  description?: string;
  config?: Record<string, unknown>;
  enabled: boolean;
  is_default?: boolean;
  plugin_id?: string;
  plugin?: PluginResponse;
}

export type Parser = {
  id: string;
  name: string;
  version: string;
  author?: string;
  description?: string;
  config?: Record<string, unknown>;
  enabled: boolean;
  plugin_id?: string;
  plugin?: PluginResponse;
}

export type IndexerResult = {
  title: string;
  link?: string;
  download_url?: string;
  guid?: string;
  pub_date?: string;
  size?: number;
  seeders?: number;
  peers?: number;
  category?: string[];
  description?: string;
  torznab_attrs?: Record<string, string>;
  indexer_name?: string;
  score?: number;
  rejections?: string[];
}
