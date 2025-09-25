// TODO: Modify once backend is ready and actual data structure is known.

export type CardItem = {
  id: string;
  title: string;
  img_url: string;
  link?: string;
};

export interface SeriesGroupItem extends CardItem {
  series: { id: string; source: string }[];
}

export interface SeriesItem extends CardItem {
  description: string;
}

export interface BookItem extends CardItem {
  description: string;
}
