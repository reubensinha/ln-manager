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
  sourceId,
  open,
  onClose,
}: {
  item: SearchSeriesResponse;
  sourceId: string;
  open: boolean;
  onClose: () => void;
}) {
  const [series, setSeries] = useState<SeriesSourceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (item) {
      getSeriesFromSource(sourceId, item.external_id).then((data) => {
        setSeries(data);
      });
    }
  }, [item, sourceId]);

    const handleAddSeries = async () => {
    if (!series) {
      return;
    }
    setIsLoading(true);
    try {
      await addSeries(sourceId, series.external_id);
      onClose();
    } catch (error) {
      console.error("Error adding series:", error);
    } finally {
      setIsLoading(false);
    }
  };


  if (!series) {
    return <Text>Loading series...</Text>;
  }

  return (
    <>
      <Modal opened={open} onClose={onClose} title="Add New Series" size="xl">
        <SeriesInfo series={series} />
        <Divider my="md" />
        {/* TODO: After API call do other procedures that are required as well. */}
        <Button fullWidth mt="xl" onClick={handleAddSeries} loading={isLoading}>
          Add Series
        </Button>
      </Modal>
    </>
  );
}

export default AddSeriesModal;
