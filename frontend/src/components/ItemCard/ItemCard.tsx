import { Link } from "react-router";
import { AspectRatio, Card, Image, Text } from "@mantine/core";
import classes from "./ItemCard.module.css";
import { type CardItem } from "../../types/CardItems";

const stripColor = "red";

function ItemCard({ item }: { item: CardItem }) {
  const link = item.link ?? "#";
  const inLibrary = item.in_library ?? true;
  const barVisible = inLibrary ? 5 : 0;
  
  return (
    <AspectRatio ratio={1 / 2} style={{ width: 400 }} mx="auto">
      <Card
        component={Link}
        to={link}
        withBorder
        radius="sm"
        style={{ overflow: "visible" }}
      >
        <Card.Section>
          <Image src={item.img_url} alt={item.title} fit="contain" />
        </Card.Section>

        {/* TODO: Add dynamic Color Strip Section once backend api is ready */}
        <Card.Section style={{ backgroundColor: stripColor, height: barVisible }} />

        <Card.Section className={classes.footer}>
          <Text fw={500} size="sm" lineClamp={3}>
            {item.title}
          </Text>
        </Card.Section>
      </Card>
    </AspectRatio>
  );
}

export default ItemCard;
