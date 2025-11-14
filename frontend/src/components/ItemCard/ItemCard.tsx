import { Link } from "react-router";
import { AspectRatio, Box, Card, Checkbox, Image, Text } from "@mantine/core";
import { useHover } from "@mantine/hooks";
import classes from "./ItemCard.module.css";
import { type CardItem } from "../../types/CardItems";

const stripColor: { [key: string]: string } = {
  true: "green",
  continuing: "cyan",
  continuing_orig: "blue",
  completed: "green",
  stalled: "orange",
  missing: "purple",
};

interface ItemCardProps {
  item: CardItem;
  selectable?: boolean;
  selectMode?: boolean;
  selected?: boolean;
  ref?: React.Ref<HTMLAnchorElement>;
  onSelect?: () => void;
}

function ItemCard({
  item,
  selectable = false,
  selectMode = false,
  selected = false,
  onSelect,
}: ItemCardProps) {
  const { hovered, ref } = useHover();
  const link = item.link ?? "#";
  const inLibrary = item.in_library ?? true;
  const barVisible = inLibrary ? 5 : 0;
  const showCheckbox = selectable && (hovered || selectMode);

  const handleClick = (e: React.MouseEvent) => {
    if (selectable && onSelect) {
      e.preventDefault();
      onSelect();
    }
  };

  return (
    <AspectRatio ratio={1 / 2} style={{ width: 400 }} mx="auto" ref={ref}>
      <Box style={{ position: "relative", height: "100%", width: "100%" }}>
        <Card
          component={Link}
          to={link}
          withBorder
          radius="sm"
          style={{
            overflow: "visible",
            cursor: "pointer",
            opacity: selected ? 0.6 : 1,
            transition: "opacity 0.2s",
          }}
          onClick={selectMode ? handleClick : undefined}
        >
          <Card.Section>
            <Image src={item.img_url} alt={item.title} fit="contain" />
          </Card.Section>

          <Card.Section
            style={{
              backgroundColor: stripColor[String(item.downloaded)] || "red",
              height: barVisible,
            }}
          />

          <Card.Section className={classes.footer}>
            <Text fw={500} size="sm" lineClamp={3}>
              {item.title}
            </Text>
          </Card.Section>
        </Card>

        {showCheckbox && (
          <Box
            style={{
              position: "absolute",
              top: 8,
              left: 8,
              zIndex: 10,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <Checkbox checked={selected} onChange={onSelect} />
          </Box>
        )}
      </Box>
    </AspectRatio>
  );
}

export default ItemCard;
