import { Link } from "react-router";
import { AspectRatio, Card, Image, Text } from "@mantine/core";
import classes from "./ItemCard.module.css";
import { type CardItem } from "../../types/CardItems";

const stripColor = "red";

// TODO: If Series, link to /series/:id if Book, link to /book/:id, else link to nothing.

function ItemCard({ item }: { item: CardItem }) {
  return (
    <AspectRatio ratio={1 / 2} style={{ width: 400 }} mx="auto">
      <Card
        component={Link}
        to={item.link ?? "#"}
        withBorder
        radius="sm"
        style={{ overflow: "visible" }}
      >
        <Card.Section>
          <Image src={item.img_url} alt={item.title} fit="contain" />
        </Card.Section>

        {/* TODO: Add dynamic Color Strip Section once backend api is ready */}
        <Card.Section style={{ backgroundColor: stripColor, height: 5 }} />

        <Card.Section className={classes.footer}>
          <Text fw={500} size="sm">
            {item.title}
          </Text>
        </Card.Section>
      </Card>
    </AspectRatio>
  );
}

export default ItemCard;
