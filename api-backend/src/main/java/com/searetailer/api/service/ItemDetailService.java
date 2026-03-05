package com.searetailer.api.service;

import com.searetailer.api.exception.ResourceNotFoundException;
import com.searetailer.api.model.dto.TopItemDetailDto;
import com.searetailer.api.model.dto.TopItemDto;
import com.searetailer.api.repository.clickhouse.MatchMapClickHouseRepository;
import com.searetailer.api.repository.clickhouse.TopItemsClickHouseRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ItemDetailService {

    private static final Logger log = LoggerFactory.getLogger(ItemDetailService.class);

    private final TopItemsClickHouseRepository topItemsRepo;
    private final MatchMapClickHouseRepository matchMapRepo;

    public ItemDetailService(TopItemsClickHouseRepository topItemsRepo,
                              MatchMapClickHouseRepository matchMapRepo) {
        this.topItemsRepo = topItemsRepo;
        this.matchMapRepo = matchMapRepo;
    }

    /**
     * Get full item detail including price history, proxy history, and matches.
     */
    public TopItemDetailDto getItemDetail(String platform, String itemId) {
        log.info("Fetching item detail: platform={}, itemId={}", platform, itemId);

        TopItemDto baseItem = topItemsRepo.findItem(platform, itemId);
        if (baseItem == null) {
            throw new ResourceNotFoundException("Item not found: " + platform + "/" + itemId);
        }

        List<TopItemDetailDto.PriceHistoryEntry> priceHistory = topItemsRepo.findPriceHistory(platform, itemId);
        List<TopItemDetailDto.ProxyHistoryEntry> proxyHistory = topItemsRepo.findProxyHistory(platform, itemId);
        List<TopItemDetailDto.MatchResultDto> matches = matchMapRepo.findMatchesForItem(platform, itemId);

        return TopItemDetailDto.builder()
                .eventDate(baseItem.getEventDate())
                .platform(baseItem.getPlatform())
                .itemId(baseItem.getItemId())
                .title(baseItem.getTitle())
                .category(baseItem.getCategory())
                .rank(baseItem.getRank())
                .url(baseItem.getUrl())
                .brandRaw(baseItem.getBrandRaw())
                .brandStd(baseItem.getBrandStd())
                .sizeValue(baseItem.getSizeValue())
                .sizeUnit(baseItem.getSizeUnit())
                .packCount(baseItem.getPackCount())
                .imageUrl(baseItem.getImageUrl())
                .listPrice(baseItem.getListPrice())
                .promoPrice(baseItem.getPromoPrice())
                .currency(baseItem.getCurrency())
                .reviewCount(baseItem.getReviewCount())
                .soldRange(baseItem.getSoldRange())
                .sourceType(baseItem.getSourceType())
                .priceHistory(priceHistory)
                .proxyHistory(proxyHistory)
                .matches(matches)
                .build();
    }
}
