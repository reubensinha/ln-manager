import { Button, Divider, Modal, Text } from "@mantine/core";

import type { SearchSeriesResponse } from "../api/ApiResponse";
import { useAddSeries, useSeriesFromSource } from "../api/hooks/series";
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
  // Only fetch the full details once the modal is open.
  const { data: series } = useSeriesFromSource(sourceId, item?.external_id, open);
  const addSeriesMutation = useAddSeries();

  const handleAddSeries = () => {
    if (!series) {
      return;
    }
    addSeriesMutation.mutate(
      { sourceId, externalId: series.external_id },
      { onSuccess: () => onClose() }
    );
  };

  return (
    <Modal opened={open} onClose={onClose} title="Add New Series" size="xl">
      {series ? (
        <>
          <SeriesInfo series={series} />
          <Divider my="md" />
          {/* TODO: After API call do other procedures that are required as well. */}
          <Button
            fullWidth
            mt="xl"
            onClick={handleAddSeries}
            loading={addSeriesMutation.isPending}
          >
            Add Series
          </Button>
        </>
      ) : (
        <Text>Loading series...</Text>
      )}
    </Modal>
  );
}

export default AddSeriesModal;
