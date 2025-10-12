// TODO: Modify once backend is ready and actual data structure is known.
export interface CardItem {
  id: string;
  title: string;
  img_url?: string;
  link?: string;
  in_library?: boolean;
  downloaded?: boolean | string;
  monitored?: boolean;
  nsfw_img?: boolean;
};