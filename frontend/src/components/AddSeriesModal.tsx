import { useEffect, useState } from "react";
import { Button, Divider, Modal, Text } from "@mantine/core";

import type {
  SearchSeriesResponse,
  SeriesSourceResponse,
} from "../api/ApiResponse";
import { getSeriesFromSource, addSeries } from "../api/api";
import SeriesInfo from "./SeriesInfo";

function AddSeriesModal({
  item,
  source,
  open,
  onClose,
}: {
  item: SearchSeriesResponse;
  source: string;
  open: boolean;
  onClose: () => void;
}) {
  const [series, setSeries] = useState<SeriesSourceResponse | null>(null);

  useEffect(() => {
    if (item) {
      getSeriesFromSource(source, item.external_id).then((data) => {
        setSeries(data);
      });
    }
  }, [item, source]);

  if (!series) {
    return <Text>Loading series...</Text>;
  }

  return (
    <>
      <Modal opened={open} onClose={onClose} title="Add New Series" size="xl">
        <SeriesInfo series={series} />
        <Divider my="md" />
        {/* TODO: Call API to add series. May include other procedures as well. */}
        <Button fullWidth mt="xl" onClick={() => {addSeries(source, series.external_id); onClose();}}>
          Add Series
        </Button>
      </Modal>
    </>
  );
}

export default AddSeriesModal;
