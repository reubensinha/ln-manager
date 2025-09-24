import {
  AspectRatio,
  Card,
  Image,
  Text,
} from "@mantine/core";
import classes from "./ItemCard.module.css";

type SeriesItem = {
  id: number;
  title: string;
  description: string;
  img_path: string;
};

// const title = "Secrets of The Silent Witch";
// const imgPath = "../../../test_img/32510.jpg";
const stripColor = "red";

function ItemCard({ series }: { series: SeriesItem }) {
  return (
    <AspectRatio ratio={1 / 2} style={{ width: 400 }} mx="auto">
      <Card withBorder radius="sm" style={{ overflow: "visible" }}>
        <Card.Section>
          {/* <AspectRatio ratio={2 / 3} style={{ width: "100%" }} mx="auto"> */}
            <Image src={series.img_path} alt={series.title} fit="contain" />
          {/* </AspectRatio> */}
        </Card.Section>

        {/* TODO: Add Color Strip Section*/}
        <Card.Section style={{ backgroundColor: stripColor, height: 5 }} />

        <Card.Section className={classes.footer}>
          <Text fw={500} size="sm">
            {series.title}
          </Text>
        </Card.Section>
      </Card>
    </AspectRatio>
  );
}

export default ItemCard;
