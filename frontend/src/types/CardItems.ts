// TODO: Modify once backend is ready and actual data structure is known.
export interface CardItem {
  id: string;
  title: string;
  img_url: string;
  link?: string;
  in_library?: boolean;
};

export interface SeriesGroupItem extends CardItem {
  series: { id: string; source: string }[];
}

