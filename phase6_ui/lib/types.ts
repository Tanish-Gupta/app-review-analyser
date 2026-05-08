export type PulseQuote = {
  theme_id: string;
  text: string;
  rating: number;
  date: string;
};

export type PulseTheme = {
  id: string;
  name: string;
  definition: string;
  review_count: number;
  volume_share: number;
  negative_share: number;
  avg_rating: number;
};

export type PulseAction = {
  owner: string;
  idea: string;
};

export type PulseData = {
  title: string;
  week: number;
  year: number;
  generated_at: string;
  review_count: number;
  avg_rating: number;
  window_start: string;
  window_end: string;
  top_themes: PulseTheme[];
  quotes: PulseQuote[];
  actions: PulseAction[];
};
